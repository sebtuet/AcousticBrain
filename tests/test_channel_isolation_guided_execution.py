from dataclasses import replace

import pytest

from acousticbrain.application import (
    ChannelIsolationGuidedExecutionService,
    evidence_acquisition_plan_fingerprint,
)
from acousticbrain.models import (
    EvidenceAcquisitionStatus,
    EvidenceAcquisitionTestType,
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan


def journey(*statuses):
    plan = ready_plan()
    preparation = record(*statuses)
    return ChannelIsolationGuidedExecutionService().build(
        plan.plan_id,
        preparation.confirmation_input.confirmation_id,
        plans=(plan,),
        registry=EvidencePlanPreparationRegistry().with_record(preparation),
    )


def test_incomplete_preparation_preserves_statuses_and_blocks_declaration_action():
    result = journey(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    assert result.preparation_status == "PREPARATION_INCOMPLETE"
    assert result.user_action_state == "REVIEW_PREPARATION_DECLARATION"
    assert tuple(
        value.status for value in result.preparation_record.confirmation_input.prerequisites
    ) == (
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )


def test_all_user_confirmed_allows_only_separate_declaration_action():
    result = journey(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    assert result.preparation_status == "PREPARATION_USER_CONFIRMED"
    assert result.user_action_state == "DECLARE_EXPERIMENT_SEPARATELY"


def test_checklist_is_an_exact_plan_projection_with_declared_channel_coverage():
    result = journey(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    plan = result.plan
    checklist = result.checklist
    assert checklist.required_inputs == plan.required_inputs
    assert checklist.independent_variables == plan.independent_variables
    assert checklist.controlled_variables == plan.controlled_variables
    assert checklist.measurements == plan.measurements_to_capture
    assert checklist.expected_observations == plan.expected_observations
    assert checklist.instructions == plan.instructions
    assert checklist.required_acquired_channels == ("LEFT", "RIGHT")
    assert checklist.required_repeated_channels == ("LEFT", "RIGHT")


def test_closed_prerequisite_guidance_never_selects_a_status():
    result = journey(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    assert tuple(value.code for value in result.prerequisite_guidance) == (
        "documented_microphone_position",
        "existing_acquisition_settings",
    )
    assert "replacer le microphone" in result.prerequisite_guidance[0].confirmed_when
    assert "Gain" in result.prerequisite_guidance[1].confirmed_when
    assert all(value.unknown_when for value in result.prerequisite_guidance)


@pytest.mark.parametrize(
    ("change", "message"),
    (
        ({"status": EvidenceAcquisitionStatus.BLOCKED}, "PLAN_NOT_READY"),
        ({"test_type": EvidenceAcquisitionTestType.REPEAT_MEASUREMENT}, "TYPE_INVALID"),
    ),
)
def test_non_ready_and_non_channel_isolation_plans_are_rejected(change, message):
    plan = replace(ready_plan(), **change)
    preparation = record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    with pytest.raises(ValueError, match=message):
        ChannelIsolationGuidedExecutionService().build(
            plan.plan_id,
            preparation.confirmation_input.confirmation_id,
            plans=(plan,),
            registry=EvidencePlanPreparationRegistry().with_record(preparation),
        )


def test_unknown_identity_and_stale_fingerprint_are_rejected():
    plan = ready_plan()
    preparation = record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    registry = EvidencePlanPreparationRegistry().with_record(preparation)
    service = ChannelIsolationGuidedExecutionService()
    with pytest.raises(ValueError, match="PLAN_UNKNOWN"):
        service.build("UNKNOWN", preparation.confirmation_input.confirmation_id, plans=(plan,), registry=registry)
    changed = replace(plan, objective="changed")
    assert evidence_acquisition_plan_fingerprint(changed) != preparation.confirmation_input.plan_contract_fingerprint
    with pytest.raises(ValueError, match="FINGERPRINT_MISMATCH"):
        service.build(changed.plan_id, preparation.confirmation_input.confirmation_id, plans=(changed,), registry=registry)
