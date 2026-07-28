import json
import wave
from pathlib import Path

import pytest

from acousticbrain.application import (
    CausalProtocolStepDeclarationService,
    ExperimentDeclarationService,
    ExperimentDiscoveryService,
)
from acousticbrain.commands.declare_causal_protocol_step import main as declare_main
from acousticbrain.persistence import MeasurementRepository
from acousticbrain.report import CausalDiscriminationPresenter, ConsoleReporter, Report

from manifest_test_data import future_manifest_extension
from test_causal_discrimination import analyze, baseline, remeasurement, speaker_swap
from test_experiment_discovery import complete_experiment


PROTOCOL = "VERIFY_SPEAKER_ROOM_ASYMMETRY"
STEP_2 = "STEP_2_SPEAKER_SWAP"
STEP_3 = "STEP_3_SIGNAL_CHAIN_SWAP"
STEP_2_CHANGED = ("LOUDSPEAKER_ASSIGNMENT",)
STEP_2_CONTROLS = (
    "LISTENING_POSITION",
    "MEASUREMENT_LEVEL",
    "MICROPHONE_POSITION",
    "ROOM_CONFIGURATION",
    "ROOM_SIDE",
    "SIGNAL_CHAIN_ASSIGNMENT",
)
STEP_3_CHANGED = ("SIGNAL_CHAIN_ASSIGNMENT",)
STEP_3_CONTROLS = ("LOUDSPEAKER_ASSIGNMENT", "ROOM_SIDE")


def ready_root(tmp_path):
    complete_experiment(tmp_path / "exp-004")
    complete_experiment(tmp_path / "exp-005")
    ExperimentDiscoveryService().discover(tmp_path)
    return tmp_path


def declare_step_2(root, **overrides):
    values = dict(
        experiment_code="exp-005",
        protocol_code=PROTOCOL,
        step_code=STEP_2,
        changed_variable_codes=STEP_2_CHANGED,
        controlled_variable_codes=STEP_2_CONTROLS,
    )
    values.update(overrides)
    return CausalProtocolStepDeclarationService().declare(root, **values)


def manifest(root):
    return json.loads((root / "exp-005/manifest.json").read_text())


def test_missing_experiment_directory_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unknown experiment directory"):
        declare_step_2(tmp_path)


def test_missing_manifest_is_rejected(tmp_path):
    complete_experiment(tmp_path / "exp-005")

    with pytest.raises(ValueError, match="Missing or invalid manifest"):
        declare_step_2(tmp_path)


def test_non_ready_experiment_is_rejected(tmp_path):
    directory = tmp_path / "exp-005"
    directory.mkdir()
    (directory / "manifest.json").write_text('{"state": "INCOMPLETE"}')

    with pytest.raises(ValueError, match="not READY"):
        declare_step_2(tmp_path)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"protocol_code": "UNKNOWN"}, "Unsupported causal protocol"),
        ({"step_code": "STEP_UNKNOWN"}, "Unsupported causal protocol step"),
        ({"step_index": 3}, "Incorrect step index"),
        ({"changed_variable_codes": ()}, "LOUDSPEAKER_ASSIGNMENT"),
        (
            {"controlled_variable_codes": ("SIGNAL_CHAIN_ASSIGNMENT",)},
            "ROOM_SIDE",
        ),
        (
            {"controlled_variable_codes": ("ROOM_SIDE",)},
            "SIGNAL_CHAIN_ASSIGNMENT",
        ),
        (
            {"observation_codes": ("UNKNOWN_OBSERVATION",)},
            "Unknown causal observation",
        ),
        (
            {
                "observation_codes": (
                    "ANOMALY_MOVED_WITH_SWAPPED_SIGNAL_CHAIN",
                )
            },
            "does not belong",
        ),
    ),
)
def test_step_2_contract_rejects_invalid_declarations(tmp_path, overrides, message):
    root = ready_root(tmp_path)

    with pytest.raises(ValueError, match=message):
        declare_step_2(root, **overrides)


@pytest.mark.parametrize(
    ("changed", "controlled", "message"),
    (
        ((), STEP_3_CONTROLS, "SIGNAL_CHAIN_ASSIGNMENT"),
        (STEP_3_CHANGED, ("LOUDSPEAKER_ASSIGNMENT",), "ROOM_SIDE"),
        (STEP_3_CHANGED, ("ROOM_SIDE",), "LOUDSPEAKER_ASSIGNMENT"),
    ),
)
def test_step_3_contract_requires_swap_and_controls(
    tmp_path, changed, controlled, message
):
    root = ready_root(tmp_path)

    with pytest.raises(ValueError, match=message):
        CausalProtocolStepDeclarationService().declare(
            root,
            experiment_code="exp-005",
            protocol_code=PROTOCOL,
            step_code=STEP_3,
            changed_variable_codes=changed,
            controlled_variable_codes=controlled,
        )


def test_changed_controlled_and_unknown_variables_must_be_disjoint(tmp_path):
    root = ready_root(tmp_path)

    with pytest.raises(ValueError, match="must be disjoint"):
        declare_step_2(
            root,
            unknown_variable_codes=("LOUDSPEAKER_ASSIGNMENT",),
        )


def test_empty_observations_are_accepted_and_never_inferred(tmp_path):
    root = ready_root(tmp_path)

    step = declare_step_2(root)

    assert step.observation_codes == ()
    assert manifest(root)["causal_protocol_step"]["observation_codes"] == []


def test_declaration_is_idempotent_and_observations_replace_the_complete_set(
    tmp_path,
):
    root = ready_root(tmp_path)
    path = root / "exp-005/manifest.json"
    declare_step_2(root)
    first = path.read_text()
    first_timestamp = path.stat().st_mtime_ns

    declare_step_2(root)
    assert path.read_text() == first
    assert path.stat().st_mtime_ns == first_timestamp

    declare_step_2(
        root,
        observation_codes=("ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER",),
    )
    assert manifest(root)["causal_protocol_step"]["observation_codes"] == [
        "ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER"
    ]

    declare_step_2(root, observation_codes=())
    assert manifest(root)["causal_protocol_step"]["observation_codes"] == []


def test_manifest_measurements_and_existing_metadata_are_preserved(tmp_path):
    root = ready_root(tmp_path)
    path = root / "exp-005/manifest.json"
    before = manifest(root)
    extension = future_manifest_extension()
    before["future_extension"] = extension
    before["custom_key"] = {"preserve": True}
    before["comparison"] = {"parent_experiment_ids": ["exp-004"]}
    MeasurementRepository.save_manifest(root / "exp-005", before)
    measurement_directory = root / "exp-005/measurements"
    (measurement_directory / "archive.mdat").write_bytes(b"REW archive fixture")
    with wave.open(str(measurement_directory / "impulse.wav"), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(48000)
        stream.writeframes(b"\x00\x00")
    measurement_paths = tuple(measurement_directory.iterdir())
    measurements_before = {
        item: (item.read_bytes(), item.stat().st_mtime_ns)
        for item in measurement_paths
    }

    declare_step_2(root)
    after = manifest(root)

    assert after["future_extension"] == extension
    assert after["custom_key"] == {"preserve": True}
    assert after["comparison"] == {"parent_experiment_ids": ["exp-004"]}
    assert after["files"] == before["files"]
    assert after["content_hash"] == before["content_hash"]
    assert {
        item: (item.read_bytes(), item.stat().st_mtime_ns)
        for item in measurement_paths
    } == measurements_before
    assert not (root / "exp-005/manifest.json.tmp").exists()


def test_discovery_reads_back_the_declared_step(tmp_path):
    root = ready_root(tmp_path)
    declare_step_2(root)

    descriptor = ExperimentDiscoveryService().discover(root)[1]

    assert descriptor.causal_protocol_step.step_code == STEP_2
    assert descriptor.causal_protocol_step.observation_codes == ()


def test_coherent_experiment_declaration_is_preserved(tmp_path):
    root = ready_root(tmp_path)
    ExperimentDeclarationService().declare(
        root,
        experiment_code="exp-005",
        experiment_kind="CONTROLLED_INTERVENTION",
        reference_experiment_code="exp-004",
        modified_variables=STEP_2_CHANGED,
        controlled_variables=STEP_2_CONTROLS,
        user_note="Permutation physique déclarée.",
    )
    declaration_before = manifest(root)["experiment_declaration"]

    declare_step_2(root)

    assert manifest(root)["experiment_declaration"] == declaration_before


def test_incoherent_experiment_declaration_is_rejected(tmp_path):
    root = ready_root(tmp_path)
    ExperimentDeclarationService().declare(
        root,
        experiment_code="exp-005",
        experiment_kind="CONTROLLED_INTERVENTION",
        reference_experiment_code="exp-004",
        modified_variables=("SIGNAL_CHAIN_ASSIGNMENT",),
        controlled_variables=tuple(
            value
            for value in STEP_2_CONTROLS
            if value != "SIGNAL_CHAIN_ASSIGNMENT"
        ),
    )

    with pytest.raises(ValueError, match="do not match"):
        declare_step_2(root)


def test_explicit_cli_note_stays_in_experiment_declaration_only(tmp_path):
    root = ready_root(tmp_path)
    ExperimentDeclarationService().declare(
        root,
        experiment_code="exp-005",
        experiment_kind="CONTROLLED_INTERVENTION",
        reference_experiment_code="exp-004",
        modified_variables=STEP_2_CHANGED,
        controlled_variables=STEP_2_CONTROLS,
    )

    declare_main([
        str(root),
        "exp-005",
        "--protocol", PROTOCOL,
        "--step", STEP_2,
        "--changed-variable", "LOUDSPEAKER_ASSIGNMENT",
        "--controlled-variable", "ROOM_SIDE",
        "--controlled-variable", "SIGNAL_CHAIN_ASSIGNMENT",
        "--note", "Permutation physique contrôlée.",
    ])
    value = manifest(root)

    assert value["experiment_declaration"]["user_note"] == (
        "Permutation physique contrôlée."
    )
    assert "user_note" not in value["causal_protocol_step"]


def test_step_without_observation_is_completed_but_resolves_no_trajectory():
    result = analyze(baseline(), remeasurement(), speaker_swap())

    assert tuple(item.step_code for item in result.completed_steps)[-1] == STEP_2
    assert result.outcome.value == "INCONCLUSIVE"
    assert result.resolved_discrimination_codes == ()
    assert result.recommended_next_protocol is None
    assert result.trace.observation_codes == (
        "LEFT_RIGHT_DIFFERENCE_REPRODUCIBLE",
    )


def test_report_marks_missing_observation_and_causal_conclusion(capsys):
    result = analyze(baseline(), remeasurement(), speaker_swap())
    presented = CausalDiscriminationPresenter().present(
        type("Context", (), {"causal_discrimination_analysis": result})()
    )
    report = Report(project_name="exp-005")
    report.causal_discrimination = presented

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert "STEP_2_SPEAKER_SWAP" in output
    assert "Observation causale : non encore qualifiée" in output
    assert "Conclusion causale : non établie" in output
    assert "Prochaine information nécessaire : qualifier l’observation" in output
    assert "ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER" not in output
    assert "ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SPEAKER_SWAP" not in output
    assert "ANOMALY_FOLLOWS_LOUDSPEAKER" not in output
    assert "ANOMALY_REMAINS_WITH_ROOM_SIDE" not in output


def test_json_order_is_deterministic(tmp_path):
    root = ready_root(tmp_path)

    declare_step_2(
        root,
        controlled_variable_codes=tuple(reversed(STEP_2_CONTROLS)),
    )

    causal = manifest(root)["causal_protocol_step"]
    assert causal["controlled_variable_codes"] == sorted(STEP_2_CONTROLS)
    assert (root / "exp-005/manifest.json").read_text().endswith("\n")
