import json
import shutil
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace

import pytest

from acousticbrain.application import (
    CausalDiscriminationService,
    CausalProtocolStepDeclarationService,
    CausalSourceComparisonAssociationService,
    ExperimentDeclarationService,
    ExperimentDiscoveryService,
)
from acousticbrain.brain import AcousticBrain
from acousticbrain.commands.associate_causal_source_comparison import (
    main as associate_main,
)
from acousticbrain.models import (
    CausalTrajectoryCode,
    CausalTrajectoryStatus,
    UnresolvedDiscrimination,
)
from acousticbrain.persistence import MeasurementRepository
from acousticbrain.report import ConsoleReporter

from historical_campaign import HISTORICAL_CAMPAIGN_ROOT
from manifest_test_data import future_manifest_extension
from test_experiment_discovery import complete_experiment


PROTOCOL_ID = "protocol.verify_speaker_room_asymmetry.v1"
HYPOTHESIS = "ASYMMETRIC_SPEAKER_ROOM_INTERACTION"
CAUSAL_PROTOCOL = "VERIFY_SPEAKER_ROOM_ASYMMETRY"
STEP_2 = "STEP_2_SPEAKER_SWAP"
STEP_3 = "STEP_3_SIGNAL_CHAIN_SWAP"
STEP_2_OBSERVATION = "ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SPEAKER_SWAP"
STEP_3_OBSERVATION = (
    "ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SIGNAL_CHAIN_SWAP"
)


def load_manifest(root, experiment_code):
    return json.loads((root / experiment_code / "manifest.json").read_text())


def save_manifest(root, experiment_code, value):
    MeasurementRepository.save_manifest(root / experiment_code, value)


def prepare_step(root, experiment_code, parent, step_code):
    if step_code == STEP_2:
        changed = ("LOUDSPEAKER_ASSIGNMENT",)
        controlled = ("ROOM_SIDE", "SIGNAL_CHAIN_ASSIGNMENT")
        observations = (STEP_2_OBSERVATION,)
    else:
        changed = ("SIGNAL_CHAIN_ASSIGNMENT",)
        controlled = ("LOUDSPEAKER_ASSIGNMENT", "ROOM_SIDE")
        observations = (STEP_3_OBSERVATION,)
    ExperimentDeclarationService().declare(
        root,
        experiment_code=experiment_code,
        experiment_kind="CONTROLLED_INTERVENTION",
        reference_experiment_code=parent,
        modified_variables=changed,
        controlled_variables=controlled,
    )
    CausalProtocolStepDeclarationService().declare(
        root,
        experiment_code=experiment_code,
        protocol_code=CAUSAL_PROTOCOL,
        step_code=step_code,
        changed_variable_codes=changed,
        controlled_variable_codes=controlled,
        observation_codes=observations,
    )


def ready_root(tmp_path):
    for code in ("exp-004", "exp-005", "exp-006"):
        complete_experiment(tmp_path / code)
    ExperimentDiscoveryService().discover(tmp_path)
    prepare_step(tmp_path, "exp-005", "exp-004", STEP_2)
    prepare_step(tmp_path, "exp-006", "exp-005", STEP_3)
    return tmp_path


def associate(root, experiment_code="exp-005", **overrides):
    values = {
        "source_protocol_id": PROTOCOL_ID,
        "source_hypothesis_code": HYPOTHESIS,
    }
    values.update(overrides)
    return CausalSourceComparisonAssociationService().associate(
        root,
        experiment_code=experiment_code,
        **values,
    )


def test_missing_directory_manifest_and_ready_state_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unknown experiment directory"):
        associate(tmp_path)

    (tmp_path / "exp-005").mkdir()
    with pytest.raises(ValueError, match="Missing or invalid manifest"):
        associate(tmp_path)

    save_manifest(tmp_path, "exp-005", {"state": "INCOMPLETE"})
    with pytest.raises(ValueError, match="not READY"):
        associate(tmp_path)


def test_comparison_and_unique_existing_parent_are_required(tmp_path):
    root = ready_root(tmp_path)
    value = load_manifest(root, "exp-005")
    value.pop("comparison")
    save_manifest(root, "exp-005", value)
    with pytest.raises(ValueError, match="Missing comparison metadata"):
        associate(root)

    value["comparison"] = {}
    save_manifest(root, "exp-005", value)
    with pytest.raises(ValueError, match="one parent"):
        associate(root)

    value["comparison"] = {"parent_experiment_ids": ["exp-003", "exp-004"]}
    save_manifest(root, "exp-005", value)
    with pytest.raises(ValueError, match="exactly one parent"):
        associate(root)

    value["comparison"] = {"parent_experiment_ids": ["missing"]}
    value["experiment_declaration"]["reference_experiment_code"] = "missing"
    save_manifest(root, "exp-005", value)
    with pytest.raises(ValueError, match="Unknown parent experiment"):
        associate(root)


@pytest.mark.parametrize(
    ("protocol", "hypothesis", "message"),
    (
        ("protocol.unknown.v1", HYPOTHESIS, "Unknown source protocol"),
        (PROTOCOL_ID, "UNKNOWN_HYPOTHESIS", "Unknown source hypothesis"),
        (
            "protocol.verify_modal_bass_persistence.v1",
            HYPOTHESIS,
            "not a supported association",
        ),
    ),
)
def test_source_protocol_and_hypothesis_contract(protocol, hypothesis, message, tmp_path):
    root = ready_root(tmp_path)
    with pytest.raises(ValueError, match=message):
        associate(
            root,
            source_protocol_id=protocol,
            source_hypothesis_code=hypothesis,
        )


def test_causal_step_is_required_and_never_inferred(tmp_path):
    root = ready_root(tmp_path)
    value = load_manifest(root, "exp-005")
    value.pop("causal_protocol_step")
    save_manifest(root, "exp-005", value)

    with pytest.raises(ValueError, match="Missing causal_protocol_step"):
        associate(root)
    descriptor = ExperimentDiscoveryService().discover(root)[1]
    assert descriptor.source_protocol_id is None
    assert descriptor.source_hypothesis_code is None


@pytest.mark.parametrize(
    ("experiment_code", "expected_step", "expected_change"),
    (
        ("exp-005", STEP_2, "CONTROLLED_LOUDSPEAKER_SWAP"),
        ("exp-006", STEP_3, "CONTROLLED_SIGNAL_CHAIN_SWAP"),
    ),
)
def test_coherent_step_association_is_accepted(
    tmp_path, experiment_code, expected_step, expected_change
):
    root = ready_root(tmp_path)
    result = associate(root, experiment_code=experiment_code)
    comparison = load_manifest(root, experiment_code)["comparison"]

    assert result.causal_step_code == expected_step
    assert comparison["source_protocol_id"] == PROTOCOL_ID
    assert comparison["source_hypothesis_code"] == HYPOTHESIS
    assert expected_change in comparison["declared_change_codes"]
    assert comparison["required_fact_codes"] == list(
        CausalSourceComparisonAssociationService.REQUIRED_FACT_CODES
    )


@pytest.mark.parametrize(
    ("experiment_code", "wrong_variable", "message"),
    (
        ("exp-005", "SIGNAL_CHAIN_ASSIGNMENT", "LOUDSPEAKER_ASSIGNMENT"),
        ("exp-006", "LOUDSPEAKER_ASSIGNMENT", "SIGNAL_CHAIN_ASSIGNMENT"),
    ),
)
def test_step_variable_mismatch_is_rejected(
    tmp_path, experiment_code, wrong_variable, message
):
    root = ready_root(tmp_path)
    value = load_manifest(root, experiment_code)
    value["causal_protocol_step"]["changed_variable_codes"] = [wrong_variable]
    save_manifest(root, experiment_code, value)

    with pytest.raises(ValueError, match=message):
        associate(root, experiment_code=experiment_code)


def test_experiment_declaration_and_parent_must_remain_coherent(tmp_path):
    root = ready_root(tmp_path)
    value = load_manifest(root, "exp-005")
    value["experiment_declaration"]["modified_variables"] = [
        "SIGNAL_CHAIN_ASSIGNMENT"
    ]
    save_manifest(root, "exp-005", value)
    with pytest.raises(ValueError, match="experiment_declaration"):
        associate(root)

    root = ready_root(tmp_path / "parent-case")
    value = load_manifest(root, "exp-005")
    value["experiment_declaration"]["reference_experiment_code"] = "exp-006"
    save_manifest(root, "exp-005", value)
    with pytest.raises(ValueError, match="reference contradicts"):
        associate(root)
    with pytest.raises(ValueError, match="Reference experiment contradicts"):
        associate(root, reference_experiment_code="exp-006")


def test_existing_manifest_and_measurement_metadata_are_preserved(tmp_path):
    root = ready_root(tmp_path)
    before = load_manifest(root, "exp-005")
    extension = future_manifest_extension()
    before["future_extension"] = extension
    before["comparison"]["parameters"] = {"existing": "preserved"}
    before["comparison"]["custom"] = {"keep": True}
    save_manifest(root, "exp-005", before)
    snapshots = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (root / "exp-005").rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }

    associate(root)
    after = load_manifest(root, "exp-005")

    assert after["future_extension"] == extension
    for key in (
        "files",
        "content_hash",
        "channel_assignments",
        "causal_protocol_step",
    ):
        assert after[key] == before[key]
    assert after["comparison"]["parameters"] == {"existing": "preserved"}
    assert after["comparison"]["custom"] == {"keep": True}
    assert snapshots == {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in snapshots
    }
    assert not (root / "exp-005/manifest.json.tmp").exists()


def test_association_is_idempotent_atomic_and_json_ordered(tmp_path):
    root = ready_root(tmp_path)
    path = root / "exp-005/manifest.json"
    associate(root)
    first = path.read_text()
    timestamp = path.stat().st_mtime_ns

    associate(root)

    assert path.read_text() == first
    assert path.stat().st_mtime_ns == timestamp
    assert first == json.dumps(
        json.loads(first), indent=2, sort_keys=True, ensure_ascii=False
    ) + "\n"
    assert not path.with_suffix(".json.tmp").exists()


def test_cli_associates_declared_parent_and_rejects_reference_conflict(
    tmp_path, capsys
):
    root = ready_root(tmp_path)
    associate_main([
        str(root),
        "exp-005",
        "--protocol", PROTOCOL_ID,
        "--hypothesis", HYPOTHESIS,
        "--reference", "exp-004",
    ])

    assert "exp-004 -> exp-005" in capsys.readouterr().out
    with pytest.raises(ValueError, match="Reference experiment contradicts"):
        associate_main([
            str(root),
            "exp-006",
            "--protocol", PROTOCOL_ID,
            "--hypothesis", HYPOTHESIS,
            "--reference", "exp-004",
        ])


def test_initial_discrimination_uses_first_explicitly_associated_local_source():
    unrelated = SimpleNamespace(
        source_protocol_id=None,
        source_hypothesis_code=None,
        unresolved_discriminations=(),
    )
    expected = (
        UnresolvedDiscrimination("LOUDSPEAKER_VS_SIGNAL_CHAIN"),
        UnresolvedDiscrimination("SIGNAL_CHAIN_VS_ROOM_SIDE"),
    )
    source = SimpleNamespace(
        source_protocol_id=PROTOCOL_ID,
        source_hypothesis_code=HYPOTHESIS,
        unresolved_discriminations=expected,
    )
    later = SimpleNamespace(
        source_protocol_id=PROTOCOL_ID,
        source_hypothesis_code=HYPOTHESIS,
        unresolved_discriminations=(),
    )
    comparison = SimpleNamespace(
        sequence=SimpleNamespace(local_comparisons=(unrelated, source, later))
    )

    assert CausalDiscriminationService._initial_discriminations(comparison) == (
        "LOUDSPEAKER_VS_SIGNAL_CHAIN",
        "SIGNAL_CHAIN_VS_ROOM_SIDE",
    )


@pytest.fixture
def real_analogue_root(tmp_path):
    measurement_root = tmp_path / "measurements"
    sources = {
        "exp-004": "baseline",
        "exp-005": "exp-001",
        "exp-006": "exp-002",
    }
    for target, source in sources.items():
        shutil.copytree(
            HISTORICAL_CAMPAIGN_ROOT / source,
            measurement_root / target,
        )
        path = measurement_root / target / "manifest.json"
        value = json.loads(path.read_text())
        for key in (
            "comparison",
            "experiment_declaration",
            "causal_protocol_step",
            "causal_discrimination_decisions",
        ):
            value.pop(key, None)
        MeasurementRepository.save_manifest(measurement_root / target, value)
    ExperimentDiscoveryService().discover(measurement_root)
    prepare_step(measurement_root, "exp-005", "exp-004", STEP_2)
    prepare_step(measurement_root, "exp-006", "exp-005", STEP_3)
    return measurement_root


def asymmetry_learning(report):
    return next(
        item
        for item in report.longitudinal_experimental_learning.states
        if item.hypothesis_code == HYPOTHESIS
    )


def test_exp005_exp006_analogue_completes_discrimination_without_causal_claim(
    real_analogue_root,
):
    before = AcousticBrain().analyze(
        measurement_root=real_analogue_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
    )
    assert before.causal_discrimination.outcome == "INCONCLUSIVE"
    assert before.causal_discrimination.new_ambiguity_codes == (
        "SOURCE_COMPARISON_UNAVAILABLE",
    )
    assert asymmetry_learning(before).learning_status == (
        "INSUFFICIENT_CAUSAL_CONTEXT"
    )

    associate(real_analogue_root, "exp-005")
    associate(real_analogue_root, "exp-006")
    after = AcousticBrain().analyze(
        measurement_root=real_analogue_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
    )

    local = {
        item.after_experiment_id: item
        for item in after.experiment_comparison.local_comparisons
    }
    cumulative = {
        item.after_experiment_id: item
        for item in after.experiment_comparison.cumulative_comparisons
    }
    for code in ("exp-005", "exp-006"):
        assert local[code].source_protocol_id == PROTOCOL_ID
        assert local[code].source_hypothesis_code == HYPOTHESIS
        assert cumulative[code].source_protocol_id == PROTOCOL_ID
        assert cumulative[code].source_hypothesis_code == HYPOTHESIS
        assert local[code].eligibility == "COMPARABLE"
    causal = after.causal_discrimination
    assert causal.new_ambiguity_codes == ()
    assert causal.outcome == "DISCRIMINATED"
    assert causal.resolved_discrimination_codes == (
        "LOUDSPEAKER_VS_SIGNAL_CHAIN",
        "SIGNAL_CHAIN_VS_ROOM_SIDE",
    )
    assert causal.remaining_discrimination_codes == ()
    assert tuple(item.trajectory_code for item in causal.compatible_trajectories) == (
        CausalTrajectoryCode.ANOMALY_REMAINS_WITH_ROOM_SIDE.value,
    )
    assert {item.trajectory_code for item in causal.contradicted_trajectories} == {
        CausalTrajectoryCode.ANOMALY_FOLLOWS_LOUDSPEAKER.value,
        CausalTrajectoryCode.ANOMALY_FOLLOWS_SIGNAL_CHAIN.value,
    }
    planning = after.experiment_planning
    assert (
        planning.recommended_candidate is None
        or planning.recommended_candidate.candidate_id
        != "experiment_candidate.asymmetric_speaker_room_interaction"
    )
    planned_asymmetry = next(
        item
        for item in planning.all_candidates
        if item.candidate_id
        == "experiment_candidate.asymmetric_speaker_room_interaction"
    )
    assert planned_asymmetry.eligible is False
    assert "CAUSAL_DISCRIMINATION_COMPLETED" in (
        planned_asymmetry.ineligibility_reasons
    )
    learning = asymmetry_learning(after)
    assert learning.learning_status == "CONFLICTING_EVIDENCE"
    assert learning.next_information_need != (
        "ASSOCIATE_SOURCE_COMPARISON_WITH_CAUSAL_PROTOCOL"
    )
    assert learning.causality_status == "NOT_ESTABLISHED"
    assert "CONFIRMED" not in {item.value for item in CausalTrajectoryStatus}
    assert "CAUSAL_NEVER_CONFIRM_TRAJECTORY" in causal.trace_applied_rule_codes

    stream = StringIO()
    with redirect_stdout(stream):
        ConsoleReporter().print(after)
    output = stream.getvalue()
    assert PROTOCOL_ID in output
    assert HYPOTHESIS in output
    assert STEP_2 in output and STEP_3 in output
    assert STEP_2_OBSERVATION in output and STEP_3_OBSERVATION in output
    assert "Résultat discriminant : DISCRIMINATED" in output
    assert "Causalité : NOT_ESTABLISHED" in output
    assert output.lower().count("expérience principale") == 1
