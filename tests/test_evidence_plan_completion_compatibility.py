from dataclasses import replace

import pytest

from acousticbrain.application import (
    EvidencePlanCompletionCompatibilityValidator,
    EvidencePlanCompletionReferenceResolver,
)
from acousticbrain.models import (
    DeterministicReasoningConclusion,
    EvidencePlanCompletionCompatibility,
    EvidencePlanCompletionCompatibilityStatus,
    EvidencePlanCompletionReferenceKind,
)
from test_deterministic_corrective_action import reasoning, synthesize
from test_evidence_plan_completion_resolution import (
    blocking_factor,
    completion_input,
    protocol,
    source_plan,
)
from test_channel_isolation_plan_coverage import plan


def protocol_action(reference_id="protocol.example.v1"):
    source_reasoning = reasoning(
        DeterministicReasoningConclusion.NON_DISCRIMINATED,
        reasoning_id="REASONING",
        target="MODAL_BASS_PERSISTENCE",
    )
    return synthesize(
        source_reasoning,
        protocols={"MODAL_BASS_PERSISTENCE": (reference_id,)},
    ).actions[0]


def plan_action(reference_id="REFERENCE_PLAN"):
    source_reasoning = reasoning(reasoning_id="REASONING")
    return synthesize(
        source_reasoning,
        plans={
            "DOMINANT_EARLY_REFLECTION_INTERACTION": (reference_id,)
        },
    ).actions[0]


def resolution(action, *, reference_kind=None, reference_id=None):
    kind = reference_kind or EvidencePlanCompletionReferenceKind.PROTOCOL
    identity = reference_id or (
        "protocol.example.v1"
        if kind is EvidencePlanCompletionReferenceKind.PROTOCOL
        else "REFERENCE_PLAN"
    )
    source = source_plan(
        corrective_action_id=action.action_id,
        reasoning_id="REASONING",
    )
    return EvidencePlanCompletionReferenceResolver().resolve(
        completion_input(
            reference_kind=kind,
            reference_id=identity,
        ),
        source_plans=(source,),
        blocking_factors=(blocking_factor(),),
        protocol_references=(protocol(identity),) if kind is (
            EvidencePlanCompletionReferenceKind.PROTOCOL
        ) else (),
        plan_references=(replace(plan(), plan_id=identity),) if kind is (
            EvidencePlanCompletionReferenceKind.PLAN
        ) else (),
    )


def validate(resolved, actions):
    return EvidencePlanCompletionCompatibilityValidator().validate(
        resolved,
        actions=actions,
    )


def test_protocol_compatibility_uses_existing_action_association_only():
    action = protocol_action()
    resolved = resolution(action)

    result = validate(resolved, (action,))

    assert result.status is (
        EvidencePlanCompletionCompatibilityStatus.REFERENCE_COMPATIBLE
    )
    assert result.source_action is action
    assert result.resolution is resolved
    assert result.authority_id == (
        "deterministic_corrective_action.compatible_reference.v1"
    )
    assert result.authority_version == 1
    assert resolved.source_plan.status.value == "BLOCKED"


def test_plan_compatibility_uses_plan_association_only():
    action = plan_action()
    resolved = resolution(
        action,
        reference_kind=EvidencePlanCompletionReferenceKind.PLAN,
    )

    result = validate(resolved, (action,))

    assert result.status.value == "REFERENCE_COMPATIBLE"
    assert result.resolution.reference.plan_id == "REFERENCE_PLAN"


def test_reference_kind_does_not_cross_compatible_collections():
    action = plan_action(reference_id="protocol.example.v1")
    resolved = resolution(action)

    with pytest.raises(
        ValueError,
        match="REFERENCE_COMPATIBILITY_NOT_ESTABLISHED",
    ):
        validate(resolved, (action,))


def test_absent_association_does_not_infer_compatibility():
    action = protocol_action(reference_id="protocol.other.v1")
    resolved = resolution(action)

    with pytest.raises(ValueError) as error:
        validate(resolved, (action,))
    assert str(error.value) == (
        "REFERENCE_COMPATIBILITY_NOT_ESTABLISHED: PROTOCOL "
        "protocol.example.v1 is not associated with action "
        f"{action.action_id}."
    )


@pytest.mark.parametrize(
    ("actions", "code"),
    (
        ((), "SOURCE_ACTION_UNKNOWN"),
        (None, "SOURCE_ACTION_AMBIGUOUS"),
    ),
)
def test_source_action_resolution_is_exact(actions, code):
    action = protocol_action()
    resolved = resolution(action)
    candidates = (action, action) if actions is None else actions
    with pytest.raises(ValueError, match=code):
        validate(resolved, candidates)


def test_source_reasoning_must_match_existing_action_authority():
    action = protocol_action()
    resolved = resolution(action)
    inconsistent = replace(
        action,
        source_reasoning_ids=("OTHER_REASONING",),
        justifications=tuple(
            replace(value, reasoning_id="OTHER_REASONING")
            for value in action.justifications
        ),
    )
    with pytest.raises(
        ValueError,
        match="REFERENCE_COMPATIBILITY_NOT_ESTABLISHED",
    ):
        validate(resolved, (inconsistent,))


def test_action_collection_order_does_not_change_compatibility():
    action = protocol_action()
    unrelated = protocol_action("protocol.unrelated.v1")
    unrelated = replace(unrelated, action_id="ACTION_UNRELATED")
    resolved = resolution(action)

    first = validate(resolved, (unrelated, action))
    second = validate(resolved, (action, unrelated))

    assert first == second


def test_compatibility_model_rejects_inconsistent_action_identity():
    action = protocol_action()
    resolved = resolution(action)
    with pytest.raises(ValueError, match="action is inconsistent"):
        EvidencePlanCompletionCompatibility(
            resolution=resolved,
            source_action=replace(action, action_id="ACTION_OTHER"),
            authority_id=EvidencePlanCompletionCompatibility.AUTHORITY_ID,
            authority_version=1,
            status=(
                EvidencePlanCompletionCompatibilityStatus.REFERENCE_COMPATIBLE
            ),
        )


def test_compatibility_model_rejects_an_unassociated_reference():
    action = protocol_action(reference_id="protocol.other.v1")
    resolved = resolution(action)
    with pytest.raises(ValueError, match="not associated"):
        EvidencePlanCompletionCompatibility(
            resolution=resolved,
            source_action=action,
            authority_id=EvidencePlanCompletionCompatibility.AUTHORITY_ID,
            authority_version=1,
            status=(
                EvidencePlanCompletionCompatibilityStatus.REFERENCE_COMPATIBLE
            ),
        )


def test_validator_requires_typed_read_only_action_collection():
    action = protocol_action()
    resolved = resolution(action)
    with pytest.raises(TypeError, match="corrective actions must be a tuple"):
        validate(resolved, [action])
