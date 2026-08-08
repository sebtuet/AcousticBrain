from dataclasses import replace
from types import SimpleNamespace

import pytest

from acousticbrain.application import evidence_acquisition_plan_fingerprint
from acousticbrain.models import (
    EvidenceAcquisitionPlanSynthesis,
    EvidenceAcquisitionStatus,
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from acousticbrain.report import (
    EvidenceAcquisitionPlanPresenter,
    GuidedGlobalStatusConsoleReporter,
    GuidedGlobalStatusPresenter,
)
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan


def report_for(*plans):
    context = SimpleNamespace(
        evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis(plans)
    )
    return SimpleNamespace(
        evidence_acquisition_plans=EvidenceAcquisitionPlanPresenter().present(context),
        experiments_discovered=SimpleNamespace(experiments=(object(), object())),
    )


def registry_with(*records):
    value = EvidencePlanPreparationRegistry()
    for item in records:
        value = value.with_record(item)
    return value


def preparation(left, right, *, confirmation_id=None):
    value = record(left, right)
    if confirmation_id is not None:
        value = replace(
            value,
            confirmation_input=replace(
                value.confirmation_input,
                confirmation_id=confirmation_id,
            ),
        )
    return value


def test_existing_recommendation_is_reused_when_registry_is_unavailable():
    plan = ready_plan()
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan), plans=(plan,)
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_UNAVAILABLE"
    assert any(plan.plan_id in line for line in result.current_state_lines)
    assert result.user_action_state == "REVIEW_RECOMMENDED_PLAN"


def test_no_plan_and_no_ready_plan_remain_distinct():
    no_plan = GuidedGlobalStatusPresenter().present(
        report_for(), plans=()
    )
    blocked = ready_plan(status=EvidenceAcquisitionStatus.BLOCKED)
    no_ready = GuidedGlobalStatusPresenter().present(
        report_for(blocked), plans=(blocked,)
    )
    assert no_plan.workflow_state == "NO_EVIDENCE_PLAN"
    assert no_ready.workflow_state == "NO_READY_EVIDENCE_PLAN"


def test_missing_preparation_routes_to_existing_draft_workflow():
    plan = ready_plan()
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=EvidencePlanPreparationRegistry(),
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_NOT_DECLARED"
    assert result.user_action_state == "GENERATE_PREPARATION_DRAFT"


def test_multiple_preparations_are_never_selected_implicitly():
    plan = ready_plan()
    first = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        confirmation_id="preparation-001",
    )
    second = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-002",
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(second, first),
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_AMBIGUOUS"
    assert result.user_action_state == "SELECT_EXACT_PREPARATION"
    assert "preparation-001, preparation-002" in result.blocker_lines[0]
    assert "--guided-preparation CONFIRMATION_ID" in result.user_action


def test_explicit_preparation_resolves_one_record_without_using_recency():
    plan = ready_plan()
    first = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        confirmation_id="preparation-001",
    )
    second = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-002",
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(second, first),
        preparation_id="preparation-001",
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_INCOMPLETE"
    assert "existing_acquisition_settings=UNKNOWN" in result.blocker_lines[0]


def test_unknown_explicit_preparation_is_rejected():
    plan = ready_plan()
    with pytest.raises(ValueError, match="one exact preparation"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=EvidencePlanPreparationRegistry(),
            preparation_id="unknown-preparation",
        )


@pytest.mark.parametrize(
    "unresolved",
    (
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        EvidencePlanPrerequisiteStatus.NOT_CONFIRMED,
    ),
)
def test_incomplete_preparation_preserves_exact_user_status(unresolved):
    plan = ready_plan()
    value = preparation(EvidencePlanPrerequisiteStatus.CONFIRMED, unresolved)
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(value),
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_INCOMPLETE"
    assert f"existing_acquisition_settings={unresolved.value}" in result.blocker_lines[0]
    assert result.user_action_state == "REVIEW_EXACT_PREPARATION"


def test_stale_preparation_is_shown_and_not_ignored():
    current = replace(ready_plan(), objective="Current exact objective")
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    assert value.confirmation_input.plan_contract_fingerprint != (
        evidence_acquisition_plan_fingerprint(current)
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(current),
        plans=(current,),
        preparation_registry=registry_with(value),
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_STALE"
    assert result.user_action_state == "GENERATE_CURRENT_PREPARATION_DRAFT"


def test_all_confirmed_routes_only_to_existing_readiness_preflight():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(value),
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_CONFIRMED"
    assert result.user_action_state == "RUN_DECLARATION_READINESS"


def test_console_always_renders_five_blocks_and_one_action(capsys):
    plan = ready_plan()
    view = GuidedGlobalStatusPresenter().present(report_for(plan), plans=(plan,))
    GuidedGlobalStatusConsoleReporter().print(view)
    output = capsys.readouterr().out
    for heading in (
        "État actuel",
        "Dernière étape validée",
        "Blocage actuel",
        "Action utilisateur",
        "Frontière scientifique",
    ):
        assert output.count(heading) == 1
    assert "Causality status: NOT_ESTABLISHED" in output
