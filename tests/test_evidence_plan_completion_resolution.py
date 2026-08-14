from dataclasses import replace

import pytest

from acousticbrain.application import EvidencePlanCompletionReferenceResolver
from acousticbrain.models import (
    EvidenceAcquisitionStatus,
    EvidenceBlockingFactor,
    EvidencePlanCompletionInput,
    EvidencePlanCompletionReferenceKind,
    EvidencePlanCompletionResolutionStatus,
    EvidencePlanCompletionResolution,
    ListeningPositionSamplingProtocol,
    REQUIRED_COMPLETION_CONDITION_CODES,
)
from test_channel_isolation_plan_coverage import plan


def completion_input(**overrides):
    values = dict(
        schema_version=1,
        completion_input_id="completion-input-001",
        source_plan_id="SOURCE_PLAN",
        reference_kind=EvidencePlanCompletionReferenceKind.PROTOCOL,
        reference_id="protocol.example.v1",
        declaration_source="USER_JSON",
    )
    values.update(overrides)
    return EvidencePlanCompletionInput(**values)


def source_plan(**overrides):
    values = dict(
        plan_id="SOURCE_PLAN",
        status=EvidenceAcquisitionStatus.BLOCKED,
        required_inputs=("compatible_protocol_or_plan_id",),
    )
    values.update(overrides)
    return replace(plan(), **values)


def blocking_factor(**overrides):
    values = dict(
        factor_id="FACTOR",
        code="MISSING_PARAMETERS",
        source_object_ids=("compatible_protocol_or_plan_id",),
        justification="An explicit compatible reference is missing.",
    )
    values.update(overrides)
    return EvidenceBlockingFactor(**values)


def protocol(protocol_id="protocol.example.v1"):
    return ListeningPositionSamplingProtocol(
        protocol_id=protocol_id,
        version=1,
        positions=(),
        modified_variables=("LISTENING_POSITION",),
        controlled_variables=("MEASUREMENT_LEVEL",),
        comparability_rule_code="SAME_ACQUISITION_SETTINGS",
        completion_condition_codes=REQUIRED_COMPLETION_CONDITION_CODES,
    )


def resolve(input_value=None, **overrides):
    arguments = dict(
        source_plans=(source_plan(),),
        blocking_factors=(blocking_factor(),),
        protocol_references=(protocol(),),
        plan_references=(),
    )
    arguments.update(overrides)
    return EvidencePlanCompletionReferenceResolver().resolve(
        input_value or completion_input(),
        **arguments,
    )


def test_exact_protocol_reference_resolution_is_identity_only():
    source = source_plan()
    reference = protocol()
    result = resolve(
        source_plans=(source,),
        protocol_references=(reference,),
    )

    assert result.status is (
        EvidencePlanCompletionResolutionStatus.REFERENCE_RESOLVED
    )
    assert result.source_plan is source
    assert result.reference is reference
    assert source.status is EvidenceAcquisitionStatus.BLOCKED


def test_exact_plan_reference_is_resolved_from_plan_collection_only():
    reference = replace(plan(), plan_id="REFERENCE_PLAN")
    result = resolve(
        completion_input(
            reference_kind=EvidencePlanCompletionReferenceKind.PLAN,
            reference_id="REFERENCE_PLAN",
        ),
        protocol_references=(protocol("REFERENCE_PLAN"),),
        plan_references=(reference,),
    )
    assert result.reference is reference


@pytest.mark.parametrize(
    ("source_plans", "code"),
    (
        ((), "SOURCE_PLAN_UNKNOWN"),
        ((source_plan(), source_plan()), "SOURCE_PLAN_AMBIGUOUS"),
    ),
)
def test_source_resolution_errors_are_explicit(source_plans, code):
    with pytest.raises(ValueError, match=code):
        resolve(source_plans=source_plans)


@pytest.mark.parametrize(
    ("protocol_references", "code"),
    (
        ((), "REFERENCE_UNKNOWN"),
        ((protocol(), protocol()), "REFERENCE_AMBIGUOUS"),
    ),
)
def test_reference_resolution_errors_are_explicit(protocol_references, code):
    with pytest.raises(ValueError, match=code):
        resolve(protocol_references=protocol_references)


def test_reference_kind_is_never_inferred_from_identifier_shape():
    with pytest.raises(ValueError, match="REFERENCE_UNKNOWN"):
        resolve(
            protocol_references=(),
            plan_references=(replace(plan(), plan_id="protocol.example.v1"),),
        )


def test_source_must_remain_blocked():
    with pytest.raises(ValueError, match="SOURCE_PLAN_NOT_BLOCKED"):
        resolve(source_plans=(source_plan(status=EvidenceAcquisitionStatus.READY),))


@pytest.mark.parametrize(
    "factor",
    (
        blocking_factor(code="CONTRADICTORY_EVIDENCE"),
        blocking_factor(source_object_ids=("another_parameter",)),
    ),
)
def test_source_must_be_blocked_by_the_exact_v1_input(factor):
    with pytest.raises(ValueError, match="SOURCE_PLAN_NOT_V1_COMPLETABLE"):
        resolve(blocking_factors=(factor,))


def test_other_resolved_blockers_are_rejected():
    other = blocking_factor(
        factor_id="OTHER_FACTOR",
        code="CONTRADICTORY_EVIDENCE",
        source_object_ids=("contradiction",),
    )
    source = source_plan(blocking_factor_ids=("FACTOR", "OTHER_FACTOR"))
    with pytest.raises(ValueError, match="SOURCE_PLAN_HAS_OTHER_BLOCKERS"):
        resolve(source_plans=(source,), blocking_factors=(blocking_factor(), other))


def test_unresolved_blocking_factor_identity_is_rejected():
    with pytest.raises(ValueError, match="blocking-factor identity"):
        resolve(blocking_factors=())


def test_resolution_is_independent_of_collection_order():
    unrelated_source = replace(plan(), plan_id="UNRELATED")
    unrelated_protocol = protocol("protocol.unrelated.v1")
    first = resolve(
        source_plans=(unrelated_source, source_plan()),
        protocol_references=(unrelated_protocol, protocol()),
    )
    second = resolve(
        source_plans=(source_plan(), unrelated_source),
        protocol_references=(protocol(), unrelated_protocol),
    )
    assert first == second


def test_resolution_requires_typed_read_only_collections():
    with pytest.raises(TypeError, match="source plans must be a tuple"):
        resolve(source_plans=[source_plan()])
    with pytest.raises(TypeError, match="protocol references contain"):
        resolve(protocol_references=(object(),))


def test_resolution_model_rejects_inconsistent_source_identity():
    resolved = resolve()
    with pytest.raises(ValueError, match="source identity is inconsistent"):
        EvidencePlanCompletionResolution(
            completion_input=resolved.completion_input,
            source_plan=replace(resolved.source_plan, plan_id="OTHER_SOURCE"),
            reference=resolved.reference,
            status=resolved.status,
        )


def test_resolution_model_rejects_inconsistent_reference_identity():
    resolved = resolve()
    with pytest.raises(ValueError, match="reference identity is inconsistent"):
        EvidencePlanCompletionResolution(
            completion_input=resolved.completion_input,
            source_plan=resolved.source_plan,
            reference=protocol("protocol.other.v1"),
            status=resolved.status,
        )
