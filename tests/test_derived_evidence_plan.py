from dataclasses import replace

import pytest

from acousticbrain.application import (
    DerivedEvidenceAcquisitionPlanFactory,
    EvidencePlanCompletionCompatibilityValidator,
    EvidencePlanCompletionReferenceResolver,
)
from acousticbrain.models import (
    DerivedEvidenceAcquisitionPlan,
    DerivedEvidencePlanStatus,
    EvidenceAcquisitionStatus,
    EvidencePlanCompletionReferenceKind,
    ListeningPositionSamplingPosition,
    ListeningPositionSamplingProtocol,
    REQUIRED_COMPLETION_CONDITION_CODES,
    REQUIRED_POSITION_MEASUREMENTS,
)
from test_channel_isolation_plan_coverage import plan
from test_evidence_plan_completion_compatibility import (
    plan_action,
    protocol_action,
)
from test_evidence_plan_completion_resolution import (
    blocking_factor,
    completion_input,
    protocol,
    source_plan,
)


def position(code, role, offset, order, *, parent=None, reference="reference"):
    return ListeningPositionSamplingPosition(
        position_code=code,
        position_role=role,
        longitudinal_offset_m=offset,
        lateral_offset_m=0.0,
        vertical_offset_m=0.0,
        parent_position_code=parent,
        reference_position_code=reference,
        acquisition_order=order,
        required_measurements=REQUIRED_POSITION_MEASUREMENTS,
    )


def complete_protocol(*, controlled_variables=("MEASUREMENT_LEVEL",)):
    return ListeningPositionSamplingProtocol(
        protocol_id="protocol.example.v1",
        version=1,
        positions=(
            position("reference", "REFERENCE", 0.0, 1),
            position("forward", "FORWARD", 0.1, 2, parent="reference"),
            position("backward", "BACKWARD", -0.1, 3, parent="forward"),
        ),
        modified_variables=("LISTENING_POSITION",),
        controlled_variables=controlled_variables,
        comparability_rule_code="SAME_ACQUISITION_SETTINGS",
        completion_condition_codes=REQUIRED_COMPLETION_CONDITION_CODES,
    )


def protocol_compatibility(*, input_value=None, reference=None, action=None):
    action = action or protocol_action()
    reference = reference or complete_protocol()
    source = source_plan(
        corrective_action_id=action.action_id,
        reasoning_id="REASONING",
    )
    resolved = EvidencePlanCompletionReferenceResolver().resolve(
        input_value or completion_input(),
        source_plans=(source,),
        blocking_factors=(blocking_factor(),),
        protocol_references=(reference,),
    )
    return EvidencePlanCompletionCompatibilityValidator().validate(
        resolved,
        actions=(action,),
    )


def plan_compatibility(*, reference_status=EvidenceAcquisitionStatus.READY):
    action = plan_action()
    source = source_plan(
        corrective_action_id=action.action_id,
        reasoning_id="REASONING",
    )
    reference = replace(
        plan(),
        plan_id="REFERENCE_PLAN",
        status=reference_status,
    )
    resolved = EvidencePlanCompletionReferenceResolver().resolve(
        completion_input(
            reference_kind=EvidencePlanCompletionReferenceKind.PLAN,
            reference_id="REFERENCE_PLAN",
        ),
        source_plans=(source,),
        blocking_factors=(blocking_factor(),),
        plan_references=(reference,),
    )
    return EvidencePlanCompletionCompatibilityValidator().validate(
        resolved,
        actions=(action,),
    )


def test_complete_protocol_creates_new_ready_plan_without_mutating_source():
    compatibility = protocol_compatibility()
    source = compatibility.resolution.source_plan

    result = DerivedEvidenceAcquisitionPlanFactory().create(compatibility)

    assert result.status is DerivedEvidencePlanStatus.DERIVED_PLAN_READY
    assert result.plan.status is EvidenceAcquisitionStatus.READY
    assert source.status is EvidenceAcquisitionStatus.BLOCKED
    assert result.plan.plan_id != source.plan_id
    assert result.plan.plan_id.startswith("DERIVED_EVIDENCE_ACQUISITION_")
    assert result.plan.required_inputs == (
        "resolved_reference:PROTOCOL:protocol.example.v1",
    )
    assert "compatible_protocol_or_plan_id" not in result.plan.required_inputs


def test_protected_source_fields_are_copied_exactly():
    result = DerivedEvidenceAcquisitionPlanFactory().create(
        protocol_compatibility()
    )
    ignored = {"plan_id", "required_inputs", "status"}
    for field in result.source_plan.__dataclass_fields__:
        if field not in ignored:
            assert getattr(result.plan, field) == getattr(result.source_plan, field)


def test_derivation_retains_complete_provenance_and_reference_parameters():
    result = DerivedEvidenceAcquisitionPlanFactory().create(
        protocol_compatibility()
    )
    assert result.source_plan_id == "SOURCE_PLAN"
    assert result.completion_input_id == "completion-input-001"
    assert result.reference_kind is EvidencePlanCompletionReferenceKind.PROTOCOL
    assert result.reference_id == "protocol.example.v1"
    assert result.compatibility_authority_id.endswith(".v1")
    assert result.compatibility_authority_version == 1
    assert result.contract_id == "acousticbrain.evidence_plan_completion_input.v1"
    assert result.contract_version == 1
    assert len(result.reference_contract_fingerprint) == 64
    assert any(
        value.startswith("position:reference:role=REFERENCE:")
        for value in result.reference_parameter_codes
    )
    assert "position_measurement:reference:LEFT" in (
        result.reference_parameter_codes
    )
    assert "completion_condition:REFERENCE_POSITION_PRESENT" in (
        result.reference_parameter_codes
    )


def test_identical_derivation_is_deterministic_and_idempotent():
    compatibility = protocol_compatibility()
    factory = DerivedEvidenceAcquisitionPlanFactory()
    first = factory.create(compatibility)
    second = factory.create(compatibility)
    assert first == second
    assert first.plan.plan_id == second.plan.plan_id


def test_semantically_different_input_produces_new_identity():
    first = DerivedEvidenceAcquisitionPlanFactory().create(
        protocol_compatibility()
    )
    second = DerivedEvidenceAcquisitionPlanFactory().create(
        protocol_compatibility(input_value=completion_input(
            completion_input_id="completion-input-002",
        ))
    )
    assert first.plan.plan_id != second.plan.plan_id


def test_changed_reference_snapshot_produces_new_identity():
    first = DerivedEvidenceAcquisitionPlanFactory().create(
        protocol_compatibility()
    )
    second = DerivedEvidenceAcquisitionPlanFactory().create(
        protocol_compatibility(reference=complete_protocol(
            controlled_variables=("GAIN", "MEASUREMENT_LEVEL"),
        ))
    )
    assert first.plan.plan_id != second.plan.plan_id


def test_incomplete_protocol_never_creates_ready_plan():
    compatibility = protocol_compatibility(reference=protocol())
    with pytest.raises(ValueError, match="REFERENCE_CONTRACT_INCOMPLETE"):
        DerivedEvidenceAcquisitionPlanFactory().create(compatibility)


def test_referenced_plan_must_already_be_ready():
    compatibility = plan_compatibility(
        reference_status=EvidenceAcquisitionStatus.BLOCKED
    )
    with pytest.raises(ValueError, match="REFERENCE_CONTRACT_INCOMPLETE"):
        DerivedEvidenceAcquisitionPlanFactory().create(compatibility)


def test_ready_plan_reference_can_create_a_typed_derivation():
    result = DerivedEvidenceAcquisitionPlanFactory().create(
        plan_compatibility()
    )
    assert result.plan.required_inputs == (
        "resolved_reference:PLAN:REFERENCE_PLAN",
    )
    assert "plan_status:READY" in result.reference_parameter_codes


def test_result_model_rejects_protected_field_changes():
    result = DerivedEvidenceAcquisitionPlanFactory().create(
        protocol_compatibility()
    )
    with pytest.raises(ValueError, match="changes protected fields: objective"):
        replace(
            result,
            plan=replace(result.plan, objective="Changed objective."),
        )


def test_result_model_rejects_unknown_compatibility_authority():
    result = DerivedEvidenceAcquisitionPlanFactory().create(
        protocol_compatibility()
    )
    with pytest.raises(ValueError, match="contract provenance is invalid"):
        replace(result, compatibility_authority_id="authority.unknown.v1")


def test_factory_has_no_persistence_side_effect_or_registry_dependency():
    compatibility = protocol_compatibility()
    source_before = compatibility.resolution.source_plan
    result = DerivedEvidenceAcquisitionPlanFactory().create(compatibility)
    assert compatibility.resolution.source_plan is source_before
    assert result.source_plan is source_before
