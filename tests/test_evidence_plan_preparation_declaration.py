import pytest

from acousticbrain.application import (
    EvidencePlanPreparationDeclarationService,
    EvidencePlanPreparationResolver,
)
from acousticbrain.models import (
    EvidencePlanAllPrerequisitesStatus,
    EvidencePlanPreparationDeclaration,
    EvidencePlanPreparationDeclarationStatus,
    EvidencePlanPrerequisiteDeclaration,
    EvidencePlanPrerequisiteStatus,
)
from test_evidence_plan_preparation_resolution import confirmation, ready_plan


def resolution(*statuses):
    source = ready_plan()
    prerequisites = tuple(
        EvidencePlanPrerequisiteDeclaration(code=code, status=status)
        for code, status in zip(source.required_inputs, statuses)
    )
    return EvidencePlanPreparationResolver().resolve(
        confirmation(source, prerequisites=prerequisites),
        plans=(source,),
    )


def test_complete_status_set_is_declared_without_claiming_all_confirmed():
    resolved = resolution(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )

    result = EvidencePlanPreparationDeclarationService().declare(resolved)

    assert result.declaration_status is (
        EvidencePlanPreparationDeclarationStatus.PREPARATION_DECLARED
    )
    assert result.all_prerequisites_status is None
    assert tuple(
        value.status for value in result.resolution.confirmation_input.prerequisites
    ) == (
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )


@pytest.mark.parametrize(
    "unconfirmed",
    (
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        EvidencePlanPrerequisiteStatus.NOT_CONFIRMED,
    ),
)
def test_unknown_and_not_confirmed_never_produce_all_confirmed(unconfirmed):
    result = EvidencePlanPreparationDeclarationService().declare(resolution(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        unconfirmed,
    ))
    assert result.all_prerequisites_status is None


def test_all_confirmed_decision_requires_every_explicit_status():
    result = EvidencePlanPreparationDeclarationService().declare(resolution(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    ))
    assert result.all_prerequisites_status is (
        EvidencePlanAllPrerequisitesStatus.ALL_PREREQUISITES_USER_CONFIRMED
    )


def test_declaration_does_not_mutate_plan_or_input():
    resolved = resolution(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    plan_before = resolved.plan.to_dict()
    input_before = resolved.confirmation_input
    EvidencePlanPreparationDeclarationService().declare(resolved)
    assert resolved.plan.to_dict() == plan_before
    assert resolved.confirmation_input is input_before


def test_empty_prerequisite_contract_is_vacuously_all_confirmed():
    source = ready_plan(required_inputs=())
    resolved = EvidencePlanPreparationResolver().resolve(
        confirmation(source), plans=(source,)
    )
    result = EvidencePlanPreparationDeclarationService().declare(resolved)
    assert result.all_prerequisites_status is (
        EvidencePlanAllPrerequisitesStatus.ALL_PREREQUISITES_USER_CONFIRMED
    )


def test_result_model_rejects_collapsed_or_inconsistent_decisions():
    resolved = resolution(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    with pytest.raises(ValueError, match="declaration status is invalid"):
        EvidencePlanPreparationDeclaration(
            resolution=resolved,
            declaration_status="PREPARATION_DECLARED",
            all_prerequisites_status=None,
        )
    with pytest.raises(ValueError, match="all-prerequisites decision is invalid"):
        EvidencePlanPreparationDeclaration(
            resolution=resolved,
            declaration_status=(
                EvidencePlanPreparationDeclarationStatus.PREPARATION_DECLARED
            ),
            all_prerequisites_status=(
                EvidencePlanAllPrerequisitesStatus.ALL_PREREQUISITES_USER_CONFIRMED
            ),
        )


def test_service_rejects_untyped_resolution():
    with pytest.raises(TypeError, match="PreparationResolution"):
        EvidencePlanPreparationDeclarationService().declare(object())
