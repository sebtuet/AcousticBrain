import pytest

from acousticbrain.application import GuidedEvidencePlanPreparationRevisionService
from acousticbrain.models import EvidencePlanPreparationRegistry, EvidencePlanPrerequisiteStatus
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import confirmation, ready_plan


def statuses(left=EvidencePlanPrerequisiteStatus.CONFIRMED, right=EvidencePlanPrerequisiteStatus.UNKNOWN):
    return {
        "documented_microphone_position": left,
        "existing_acquisition_settings": right,
    }


def test_revision_preserves_source_and_applies_every_explicit_status():
    plan = ready_plan()
    source = confirmation(plan)
    result = GuidedEvidencePlanPreparationRevisionService().revise(
        source, statuses(), plans=(plan,), registry=EvidencePlanPreparationRegistry()
    )
    assert source == confirmation(plan)
    assert result.confirmation_input.confirmation_id.endswith("-1")
    assert result.confirmation_input.confirmation_id != source.confirmation_id
    assert {value.code: value.status for value in result.confirmation_input.prerequisites} == statuses()
    assert result.confirmation_input.plan_contract_fingerprint == source.plan_contract_fingerprint


def test_registry_and_source_identity_allocate_next_free_ordinal():
    plan = ready_plan()
    source = confirmation(plan, confirmation_id="preparation-" + "x" * 12 + "-source")
    existing = record(EvidencePlanPrerequisiteStatus.CONFIRMED, EvidencePlanPrerequisiteStatus.UNKNOWN)
    prefix = f"preparation-{source.plan_contract_fingerprint[:12]}-"
    existing = type(existing)(
        confirmation_input=type(source)(**{**source.__dict__, "confirmation_id": prefix + "1"}),
        resolution_status=existing.resolution_status,
        declaration_status=existing.declaration_status,
        all_prerequisites_status=existing.all_prerequisites_status,
    )
    result = GuidedEvidencePlanPreparationRevisionService().revise(
        source, statuses(), plans=(plan,),
        registry=EvidencePlanPreparationRegistry().with_record(existing),
    )
    assert result.confirmation_input.confirmation_id == prefix + "2"


@pytest.mark.parametrize(
    "value",
    (
        {"documented_microphone_position": EvidencePlanPrerequisiteStatus.UNKNOWN},
        {**statuses(), "extra": EvidencePlanPrerequisiteStatus.UNKNOWN},
    ),
)
def test_missing_and_extra_statuses_are_rejected(value):
    plan = ready_plan()
    with pytest.raises(ValueError, match="STATUS_SET_MISMATCH"):
        GuidedEvidencePlanPreparationRevisionService().revise(
            confirmation(plan), value, plans=(plan,), registry=EvidencePlanPreparationRegistry()
        )
