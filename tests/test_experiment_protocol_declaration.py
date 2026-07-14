import json

import pytest

from acousticbrain.application import ExperimentProtocolDeclarationService


def test_user_confirmation_writes_modal_campaign_without_inventing_measurements(
    tmp_path,
):
    for experiment_id in ("exp-003", "exp-004", "exp-005"):
        directory = tmp_path / experiment_id
        directory.mkdir()
        (directory / "manifest.json").write_text(
            json.dumps({"experiment_id": experiment_id, "files": []}),
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
