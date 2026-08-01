from dataclasses import replace
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.report import (
    DeterministicCorrectiveActionPresenter,
    EvidenceAcquisitionPlanPresenter,
    EvidencePlanUserViewConsoleReporter,
    EvidencePlanUserViewPresenter,
)
from test_evidence_plan_completion_compatibility import protocol_action
from test_evidence_plan_completion_resolution import blocking_factor, source_plan


def report(*, compatible_protocol_ids=()):
    action = replace(
        protocol_action(),
        compatible_protocol_ids=compatible_protocol_ids,
    )
    plan = source_plan(
        corrective_action_id=action.action_id,
        reasoning_id="REASONING",
    )
    presented_plans = EvidenceAcquisitionPlanPresenter().present(SimpleNamespace(
        evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(plan,)),
    ))
    presented_actions = DeterministicCorrectiveActionPresenter().present(
        SimpleNamespace(
            deterministic_corrective_action_synthesis=SimpleNamespace(
                actions=(action,)
            )
        )
    )
    factor = blocking_factor()
    presented_factor = SimpleNamespace(
        factor_id=factor.factor_id,
        code=factor.code,
        source_object_ids=factor.source_object_ids,
        justification=factor.justification,
    )
    return SimpleNamespace(
        evidence_acquisition_plans=presented_plans,
        deterministic_corrective_actions=presented_actions,
        deterministic_evidence_weighting=SimpleNamespace(weights=(
            SimpleNamespace(blocking_factors=(presented_factor,)),
        )),
    )


def test_blocked_plan_without_authority_does_not_transfer_expertise_to_user():
    view = EvidencePlanUserViewPresenter().present(report(), "SOURCE_PLAN")

    assert view.plan_status == "BLOCKED"
    assert view.user_action_state == "EXPERT_VALIDATION_REQUIRED"
    assert view.user_action == (
        "Aucune action sûre pour vous : faire établir une référence compatible "
        "par une source scientifique ou un acousticien."
    )
    assert view.causality_status == "NOT_ESTABLISHED"
    assert any("compatible_protocol_or_plan_id" in line for line in view.blocker_lines)


def test_existing_compatible_authority_is_displayed_without_selecting_it():
    view = EvidencePlanUserViewPresenter().present(
        report(compatible_protocol_ids=("protocol.example.v1",)),
        "SOURCE_PLAN",
    )

    assert view.user_action_state == "SUBMIT_STRUCTURED_COMPLETION_INPUT"
    assert view.user_action.endswith("protocol.example.v1")


def test_unknown_and_ambiguous_plan_id_are_explicit():
    value = report()
    with pytest.raises(ValueError, match="Unknown evidence plan_id"):
        EvidencePlanUserViewPresenter().present(value, "UNKNOWN")
    value.evidence_acquisition_plans = SimpleNamespace(
        plans=value.evidence_acquisition_plans.plans * 2
    )
    with pytest.raises(ValueError, match="Ambiguous evidence plan_id"):
        EvidencePlanUserViewPresenter().present(value, "SOURCE_PLAN")


def test_missing_blocker_detail_is_shown_as_unavailable():
    value = report()
    value.deterministic_evidence_weighting = SimpleNamespace(weights=())
    view = EvidencePlanUserViewPresenter().present(value, "SOURCE_PLAN")
    assert view.blocker_lines == ("FACTOR : détail indisponible.",)


def test_console_always_renders_the_four_contractual_blocks(capsys):
    value = report()
    value.evidence_plan_user_view = EvidencePlanUserViewPresenter().present(
        value, "SOURCE_PLAN"
    )
    EvidencePlanUserViewConsoleReporter().print(value)
    output = capsys.readouterr().out
    assert "Intention\n" in output
    assert "Pourquoi le plan est bloqué\n" in output
    assert "Action utilisateur\n" in output
    assert "Frontière scientifique\n" in output
    assert "Causality status: NOT_ESTABLISHED" in output


def test_main_run_requests_existing_syntheses_and_projects_one_plan():
    value = report()
    calls = []
    brain = SimpleNamespace(analyze=lambda **arguments: (
        calls.append(arguments) or value
    ))
    reporter = SimpleNamespace(reports=[], print=lambda item: reporter.reports.append(item))

    result = acousticbrain_main.run(
        SimpleNamespace(resolve=lambda: "/measurements"),
        evidence_plan_view="SOURCE_PLAN",
        brain=brain,
        reporter=reporter,
    )

    assert calls[0]["synthesize_evidence_acquisition"] is True
    assert result.evidence_plan_user_view.plan_id == "SOURCE_PLAN"
    assert reporter.reports == [result]
