import json
from dataclasses import replace

import pytest

from acousticbrain.application import ChannelIsolationOperationalWorksheetService
from acousticbrain.models import EvidenceAcquisitionStatus, EvidenceAcquisitionTestType
from acousticbrain.persistence import ChannelIsolationMicrophonePositionRecordJsonLoader
from test_evidence_plan_preparation_resolution import ready_plan


def test_generation_preserves_exact_plan_and_uses_explicit_placeholders():
    plan = ready_plan()
    before = plan.to_dict()
    result = ChannelIsolationOperationalWorksheetService().generate(
        plan.plan_id, plans=(plan,)
    )
    assert result.microphone_position["plan_id"] == plan.plan_id
    assert result.microphone_position["reference_geometry"] == (
        "REPLACE_WITH_EXPLICIT_USER_VALUE"
    )
    assert result.acquisition_settings["reuse_declaration"].startswith(
        "REPLACE_WITH_"
    )
    assert plan.to_dict() == before


@pytest.mark.parametrize(
    ("plan", "message"),
    (
        (replace(ready_plan(), status=EvidenceAcquisitionStatus.BLOCKED), "NOT_READY"),
        (
            replace(
                ready_plan(),
                test_type=EvidenceAcquisitionTestType.REPEAT_MEASUREMENT,
            ),
            "TYPE_INVALID",
        ),
    ),
)
def test_non_ready_and_wrong_type_plans_are_rejected(plan, message):
    with pytest.raises(ValueError, match=message):
        ChannelIsolationOperationalWorksheetService().generate(
            plan.plan_id, plans=(plan,)
        )


def test_worksheet_export_is_atomic_and_refuses_overwrite(tmp_path):
    result = ChannelIsolationOperationalWorksheetService().generate(
        "READY_PLAN", plans=(ready_plan(),)
    )
    path = tmp_path / "microphone.json"
    loader = ChannelIsolationMicrophonePositionRecordJsonLoader()
    loader.save_new_worksheet(path, result.microphone_position)
    assert json.loads(path.read_text(encoding="utf-8")) == result.microphone_position
    with pytest.raises(ValueError, match="already exists"):
        loader.save_new_worksheet(path, result.microphone_position)
