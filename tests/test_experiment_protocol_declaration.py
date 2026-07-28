import json

import pytest

from acousticbrain.application import ExperimentProtocolDeclarationService

from manifest_test_data import future_manifest_extension


def test_user_confirmation_writes_modal_campaign_without_inventing_measurements(
    tmp_path,
):
    extension = future_manifest_extension()
    for experiment_id in ("exp-003", "exp-004", "exp-005"):
        directory = tmp_path / experiment_id
        directory.mkdir()
        (directory / "manifest.json").write_text(
            json.dumps(
                {
                    "experiment_id": experiment_id,
                    "files": [],
                    "future_extension": extension,
                }
            ),
            encoding="utf-8",
        )

    result = ExperimentProtocolDeclarationService().confirm_modal_multi_position(
        tmp_path,
        reference_experiment_id="exp-003",
        reference_parent_experiment_id="exp-002",
        listening_position_offsets_m={
            "exp-003": 0.0,
            "exp-004": -0.3,
            "exp-005": 0.3,
        },
    )

    assert result == ("exp-003", "exp-004", "exp-005")
    reference = json.loads((tmp_path / "exp-003/manifest.json").read_text())
    backward = json.loads((tmp_path / "exp-004/manifest.json").read_text())
    forward = json.loads((tmp_path / "exp-005/manifest.json").read_text())
    assert reference["comparison"]["parent_experiment_ids"] == ["exp-002"]
    assert backward["comparison"]["parent_experiment_ids"] == ["exp-003"]
    assert forward["comparison"]["parent_experiment_ids"] == ["exp-003"]
    assert reference["comparison"]["parameters"] == {
        "listening_position_offset_m": 0.0,
        "position_role": "REFERENCE",
    }
    assert backward["comparison"]["parameters"]["position_role"] == "BACKWARD"
    assert forward["comparison"]["parameters"]["position_role"] == "FORWARD"
    assert forward["experiment_id"] == "exp-005"
    assert forward["files"] == []
    assert all(
        manifest["future_extension"] == extension
        for manifest in (reference, backward, forward)
    )


def test_confirmation_rejects_missing_or_invented_protocol_facts(tmp_path):
    (tmp_path / "exp-003").mkdir()

    with pytest.raises(ValueError, match="another position"):
        ExperimentProtocolDeclarationService().confirm_modal_multi_position(
            tmp_path,
            reference_experiment_id="exp-003",
            reference_parent_experiment_id="exp-002",
            listening_position_offsets_m={"exp-003": 0.0},
        )

    with pytest.raises(ValueError, match="Unknown experiment directories"):
        ExperimentProtocolDeclarationService().confirm_modal_multi_position(
            tmp_path,
            reference_experiment_id="exp-003",
            reference_parent_experiment_id="exp-002",
            listening_position_offsets_m={"exp-003": 0.0, "exp-004": -0.3},
        )


def test_user_confirmation_declares_auditable_temporary_speaker_move(tmp_path):
    extension = future_manifest_extension()
    for experiment_id in ("reference", "speaker-moved"):
        directory = tmp_path / experiment_id
        directory.mkdir()
        (directory / "manifest.json").write_text(
            json.dumps(
                {
                    "experiment_id": experiment_id,
                    "files": [],
                    "future_extension": extension,
                }
            ),
            encoding="utf-8",
        )

    result = ExperimentProtocolDeclarationService().confirm_temporary_speaker_move(
        tmp_path,
        reference_experiment_id="reference",
        moved_experiment_id="speaker-moved",
        speaker_id="LEFT",
        surface_id="FRONT_WALL",
        geometry_candidate_id="sbir-path-left-front",
        displacement_m=0.10,
    )

    assert result == "speaker-moved"
    reference = json.loads((tmp_path / "reference/manifest.json").read_text())
    moved = json.loads((tmp_path / "speaker-moved/manifest.json").read_text())
    assert reference == {
        "experiment_id": "reference",
        "files": [],
        "future_extension": extension,
    }
    assert moved["experiment_id"] == "speaker-moved"
    assert moved["files"] == []
    assert moved["future_extension"] == extension
    comparison = moved["comparison"]
    assert comparison["parent_experiment_ids"] == ["reference"]
    assert comparison["source_protocol_id"] == "protocol.temporary_move_speaker.v1"
    assert comparison["source_hypothesis_code"] == "SBIR_PLACEMENT_INTERACTION"
    assert comparison["declared_change_codes"] == [
        "CONTROLLED_SPEAKER_POSITION",
        "TEMPORARY_SPEAKER_MOVE",
    ]
    assert comparison["required_fact_codes"] == [
        "sbir.target_null_frequency_hz",
        "sbir.target_null_prominence_db",
    ]
    parameters = comparison["parameters"]
    assert parameters["speaker_id"] == "LEFT"
    assert parameters["surface_id"] == "FRONT_WALL"
    assert parameters["geometry_candidate_id"] == "sbir-path-left-front"
    assert parameters["speaker_displacement_m"] == 0.10
    assert parameters["controlled_variable_codes"] == [
        "MICROPHONE_POSITION",
        "LOUDSPEAKER_ORIENTATION",
        "OTHER_LOUDSPEAKER_POSITIONS",
        "SIGNAL_CHAIN_ASSIGNMENT",
        "MEASUREMENT_LEVEL",
        "ROOM_CONFIGURATION",
    ]
    assert parameters["changed_variable_codes"] == ["LOUDSPEAKER_POSITION"]
    assert parameters["expected_observation_codes"] == [
        "SBIR_MOVES_WITH_SPEAKER",
        "SBIR_REMAINS_FIXED",
    ]


@pytest.mark.parametrize("displacement", [0.0, float("inf"), True, "0.1"])
def test_temporary_speaker_move_rejects_invalid_displacement(
    tmp_path,
    displacement,
):
    (tmp_path / "reference").mkdir()
    (tmp_path / "speaker-moved").mkdir()

    with pytest.raises(ValueError, match="finite and non-zero"):
        ExperimentProtocolDeclarationService().confirm_temporary_speaker_move(
            tmp_path,
            reference_experiment_id="reference",
            moved_experiment_id="speaker-moved",
            speaker_id="LEFT",
            surface_id="FRONT_WALL",
            geometry_candidate_id="candidate",
            displacement_m=displacement,
        )


def test_temporary_speaker_move_requires_existing_measurements(tmp_path):
    (tmp_path / "reference").mkdir()

    with pytest.raises(ValueError, match="speaker-moved"):
        ExperimentProtocolDeclarationService().confirm_temporary_speaker_move(
            tmp_path,
            reference_experiment_id="reference",
            moved_experiment_id="speaker-moved",
            speaker_id="LEFT",
            surface_id="FRONT_WALL",
            geometry_candidate_id="candidate",
            displacement_m=0.1,
        )
