from dataclasses import replace

import pytest

from acousticbrain.application import (
    EvidencePlanPreparationResolver,
    evidence_acquisition_plan_fingerprint,
)
from acousticbrain.models import (
    EvidenceAcquisitionStatus,
    EvidencePlanPreparationConfirmationInput,
    EvidencePlanPreparationResolution,
    EvidencePlanPreparationResolutionStatus,
    EvidencePlanPrerequisiteDeclaration,
    EvidencePlanPrerequisiteStatus,
)
from test_channel_isolation_plan_coverage import plan


def ready_plan(**changes):
    values = {
        "plan_id": "READY_PLAN",
        "status": EvidenceAcquisitionStatus.READY,
        "required_inputs": (
            "documented_microphone_position",
            "existing_acquisition_settings",
        ),
    }
    values.update(changes)
    return replace(plan(), **values)


def confirmation(source=None, **changes):
    source = source or ready_plan()
    values = {
        "schema_version": 1,
        "confirmation_id": "preparation-confirmation-001",
        "plan_id": source.plan_id,
        "plan_contract_fingerprint": evidence_acquisition_plan_fingerprint(source),
        "prerequisites": tuple(
            EvidencePlanPrerequisiteDeclaration(
                code=code,
                status=EvidencePlanPrerequisiteStatus.UNKNOWN,
            )
            for code in reversed(source.required_inputs)
        ),
        "declaration_source": "USER_JSON",
    }
    values.update(changes)
    return EvidencePlanPreparationConfirmationInput(**values)


def test_exact_ready_plan_and_complete_prerequisite_set_are_resolved():
    source = ready_plan()
    source_before = source.to_dict()

    result = EvidencePlanPreparationResolver().resolve(
        confirmation(source), plans=(source,)
    )

    assert result.status is EvidencePlanPreparationResolutionStatus.PLAN_EXACTLY_RESOLVED
    assert result.plan is source
    assert result.plan.to_dict() == source_before
    assert result.plan.status is EvidenceAcquisitionStatus.READY


def test_collection_and_prerequisite_order_do_not_change_resolution():
    source = ready_plan()
    unrelated = replace(source, plan_id="UNRELATED")
    first = EvidencePlanPreparationResolver().resolve(
        confirmation(source), plans=(unrelated, source)
    )
    second = EvidencePlanPreparationResolver().resolve(
        confirmation(source), plans=(source, unrelated)
    )
    assert first == second


@pytest.mark.parametrize(
    "plans, message",
    (
        ((), "PREPARATION_PLAN_UNKNOWN"),
        ((ready_plan(), ready_plan()), "PREPARATION_PLAN_AMBIGUOUS"),
    ),
)
def test_unknown_and_ambiguous_plan_identity_are_explicit(plans, message):
    with pytest.raises(ValueError, match=message):
        EvidencePlanPreparationResolver().resolve(
            confirmation(), plans=plans
        )


@pytest.mark.parametrize(
    "status",
    (EvidenceAcquisitionStatus.BLOCKED, EvidenceAcquisitionStatus.PROPOSED),
)
def test_non_ready_plan_is_rejected_without_promotion(status):
    source = ready_plan(status=status)
    before = source.to_dict()
    with pytest.raises(ValueError, match="PREPARATION_PLAN_NOT_READY"):
        EvidencePlanPreparationResolver().resolve(
            confirmation(source), plans=(source,)
        )
    assert source.to_dict() == before
    assert source.status is status


def test_stale_or_different_plan_snapshot_is_rejected():
    original = ready_plan()
    changed = replace(original, objective="Different exact objective.")
    input_value = confirmation(original)
    with pytest.raises(ValueError, match="PLAN_CONTRACT_FINGERPRINT_MISMATCH"):
        EvidencePlanPreparationResolver().resolve(
            input_value, plans=(changed,)
        )


@pytest.mark.parametrize(
    "codes, expected",
    (
        (("documented_microphone_position",), "missing: existing_acquisition_settings"),
        (
            (
                "documented_microphone_position",
                "existing_acquisition_settings",
                "invented",
            ),
            "extra: invented",
        ),
        (("invented",), "missing: documented_microphone_position, existing_acquisition_settings; extra: invented"),
    ),
)
def test_prerequisite_set_mismatch_reports_sorted_details(codes, expected):
    source = ready_plan()
    prerequisites = tuple(
        EvidencePlanPrerequisiteDeclaration(
            code=code,
            status=EvidencePlanPrerequisiteStatus.UNKNOWN,
        )
        for code in codes
    )
    with pytest.raises(ValueError) as caught:
        EvidencePlanPreparationResolver().resolve(
            confirmation(source, prerequisites=prerequisites),
            plans=(source,),
        )
    assert expected in str(caught.value)


def test_empty_required_input_contract_resolves_only_empty_declaration():
    source = ready_plan(required_inputs=())
    result = EvidencePlanPreparationResolver().resolve(
        confirmation(source), plans=(source,)
    )
    assert result.confirmation_input.prerequisites == ()


def test_fingerprint_is_deterministic_and_sensitive_to_full_plan_contract():
    source = ready_plan()
    assert evidence_acquisition_plan_fingerprint(source) == (
        evidence_acquisition_plan_fingerprint(replace(source))
    )
    assert evidence_acquisition_plan_fingerprint(source) != (
        evidence_acquisition_plan_fingerprint(
            replace(source, controlled_variables=("different",))
        )
    )


def test_result_model_rejects_inconsistent_identity_or_status():
    source = ready_plan()
    input_value = confirmation(source)
    with pytest.raises(ValueError, match="identity is inconsistent"):
        EvidencePlanPreparationResolution(
            confirmation_input=input_value,
            plan=replace(source, plan_id="OTHER"),
            status=EvidencePlanPreparationResolutionStatus.PLAN_EXACTLY_RESOLVED,
        )
    with pytest.raises(ValueError, match="status is invalid"):
        EvidencePlanPreparationResolution(
            confirmation_input=input_value,
            plan=source,
            status="PLAN_EXACTLY_RESOLVED",
        )


def test_untyped_input_and_plan_collection_are_rejected():
    resolver = EvidencePlanPreparationResolver()
    with pytest.raises(TypeError, match="ConfirmationInput"):
        resolver.resolve(object(), plans=())
    with pytest.raises(TypeError, match="typed tuple"):
        resolver.resolve(confirmation(), plans=[ready_plan()])
