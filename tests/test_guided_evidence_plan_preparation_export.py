import json

import pytest

from acousticbrain.application import GuidedEvidencePlanPreparationDraftService
from acousticbrain.models import EvidencePlanPreparationRegistry
from acousticbrain.persistence import EvidencePlanPreparationConfirmationJsonLoader
from test_evidence_plan_preparation_resolution import ready_plan


def draft_input():
    plan = ready_plan()
    return GuidedEvidencePlanPreparationDraftService().generate(
        plan.plan_id,
        plans=(plan,),
        registry=EvidencePlanPreparationRegistry(),
    ).confirmation_input


def test_canonical_export_round_trips_through_existing_strict_loader():
    loader = EvidencePlanPreparationConfirmationJsonLoader()
    value = draft_input()
    payload = loader.dumps(value)
    assert loader.decode(json.loads(payload)) == value
    assert payload == loader.dumps(value)
    assert '"status": "UNKNOWN"' in payload
    assert '"user_note": null' in payload


def test_explicit_new_file_export_is_complete_and_atomic(tmp_path):
    loader = EvidencePlanPreparationConfirmationJsonLoader()
    value = draft_input()
    path = tmp_path / "draft.json"
    assert loader.save_new(path, value) == path
    assert loader.load(path) == value
    assert not path.with_suffix(".json.tmp").exists()


def test_export_refuses_overwrite_without_changing_existing_file(tmp_path):
    path = tmp_path / "draft.json"
    path.write_text("user content\n", encoding="utf-8")
    with pytest.raises(ValueError, match="already exists"):
        EvidencePlanPreparationConfirmationJsonLoader().save_new(
            path, draft_input()
        )
    assert path.read_text(encoding="utf-8") == "user content\n"


def test_export_refuses_missing_parent_without_creating_it(tmp_path):
    path = tmp_path / "missing" / "draft.json"
    with pytest.raises(ValueError, match="parent is unavailable"):
        EvidencePlanPreparationConfirmationJsonLoader().save_new(
            path, draft_input()
        )
    assert not path.parent.exists()
