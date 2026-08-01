from dataclasses import replace

import pytest

from acousticbrain.application import (
    GuidedEvidencePlanPreparationDraftService,
    evidence_acquisition_plan_fingerprint,
)
from acousticbrain.models import (
    EvidenceAcquisitionStatus,
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan


def test_draft_copies_exact_ready_contract_with_only_unknown_defaults():
    plan = ready_plan()
    before = plan.to_dict()
    result = GuidedEvidencePlanPreparationDraftService().generate(
        plan.plan_id,
        plans=(plan,),
        registry=EvidencePlanPreparationRegistry(),
    )
    value = result.confirmation_input
    assert value.plan_id == plan.plan_id
    assert value.plan_contract_fingerprint == evidence_acquisition_plan_fingerprint(plan)
    assert value.confirmation_id == (
        f"preparation-{value.plan_contract_fingerprint[:12]}-1"
    )
    assert tuple(item.code for item in value.prerequisites) == tuple(
        sorted(plan.required_inputs)
    )
    assert all(
        item.status is EvidencePlanPrerequisiteStatus.UNKNOWN
        for item in value.prerequisites
    )
    assert value.declaration_source == "GUIDED_USER_CONFIRMATION"
    assert value.user_note is None
    assert plan.to_dict() == before


def test_identity_allocation_is_stable_and_uses_smallest_free_ordinal():
    plan = ready_plan()
    service = GuidedEvidencePlanPreparationDraftService()
    first = service.generate(
        plan.plan_id, plans=(plan,), registry=EvidencePlanPreparationRegistry()
    )
    existing = replace(
        record(
            EvidencePlanPrerequisiteStatus.CONFIRMED,
            EvidencePlanPrerequisiteStatus.UNKNOWN,
        ),
        confirmation_input=replace(
            first.confirmation_input,
            confirmation_id=first.confirmation_input.confirmation_id,
        ),
    )
    registry = EvidencePlanPreparationRegistry().with_record(existing)
    second = service.generate(plan.plan_id, plans=(plan,), registry=registry)
    repeated = service.generate(plan.plan_id, plans=(plan,), registry=registry)
    assert second == repeated
    assert second.confirmation_input.confirmation_id.endswith("-2")


@pytest.mark.parametrize(
    ("plans", "message"),
    (
        ((), "PLAN_UNKNOWN"),
        ((ready_plan(), ready_plan()), "PLAN_AMBIGUOUS"),
        (
            (replace(ready_plan(), status=EvidenceAcquisitionStatus.BLOCKED),),
            "PLAN_NOT_READY",
        ),
    ),
)
def test_unknown_ambiguous_and_non_ready_plans_are_rejected(plans, message):
    with pytest.raises(ValueError, match=message):
        GuidedEvidencePlanPreparationDraftService().generate(
            "READY_PLAN",
            plans=plans,
            registry=EvidencePlanPreparationRegistry(),
        )


def test_generation_writes_no_registry_measurement_or_manifest(tmp_path):
    plan = ready_plan()
    registry = EvidencePlanPreparationRegistry()
    GuidedEvidencePlanPreparationDraftService().generate(
        plan.plan_id, plans=(plan,), registry=registry
    )
    assert registry == EvidencePlanPreparationRegistry()
    assert tuple(tmp_path.rglob("*")) == ()
