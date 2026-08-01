from dataclasses import replace
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.report import (
    DeterministicCorrectiveActionPresenter,
    EvidenceAcquisitionPlanPresenter,
    EvidencePlanOverviewConsoleReporter,
    EvidencePlanOverviewPresenter,
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


def test_readable_label_uses_closed_vocabulary_without_changing_contract():
    value = report()
    original = value.evidence_acquisition_plans.plans[0]
    contractual_objective = original.objective
    value.evidence_acquisition_plans = SimpleNamespace(plans=(replace(
        original,
        reasoning_id="MODAL_BASS_PERSISTENCE_REASONING",
        test_type="PARAMETER_COMPLETION",
    ),))

    view = EvidencePlanUserViewPresenter().present(value, "SOURCE_PLAN")

    assert view.user_label == (
        "Persistance modale dans le grave — compléter un prérequis documentaire"
    )
    assert view.intention_lines[0] == contractual_objective


def test_unknown_vocabulary_has_neutral_deterministic_fallback():
    view = EvidencePlanUserViewPresenter().present(report(), "SOURCE_PLAN")
    assert view.user_label == (
        "Plan d’acquisition de preuves — vérifier séparément les canaux"
    )


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
    assert "État du plan\n" in output
    assert "Préparation déclarée\n" in output
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


def test_overview_lists_every_plan_in_stable_order_without_selection():
    value = report()
    original = value.evidence_acquisition_plans.plans[0]
    second = replace(original, plan_id="AAA_PLAN", status="READY")
    value.evidence_acquisition_plans = SimpleNamespace(
        plans=(original, second)
    )

    overview = EvidencePlanOverviewPresenter().present(value)

    assert tuple(item.plan_id for item in overview.plans) == (
        "AAA_PLAN", "SOURCE_PLAN"
    )
    assert overview.plans[0].user_action_state == (
        "VERIFY_DECLARED_PREREQUISITES"
    )
    assert overview.plans[1].user_action_state == "EXPERT_VALIDATION_REQUIRED"
    assert overview.causality_status == "NOT_ESTABLISHED"


def test_ready_plan_exposes_only_its_declared_preparation_contract():
    value = report()
    original = value.evidence_acquisition_plans.plans[0]
    ready = replace(
        original,
        status="READY",
        required_inputs=("documented_microphone_position", "same_gain"),
        independent_variables=("active_channel",),
        controlled_variables=("gain", "microphone_position"),
        measurements_to_capture=("left_response", "right_response"),
        expected_observations=("channel_difference",),
        instructions=("Measure left.", "Measure right."),
        success_criteria=("Difference is repeatable.",),
        failure_criteria=("Gain changed.",),
        limitations=("Causality is not established.",),
    )
    value.evidence_acquisition_plans = SimpleNamespace(plans=(ready,))

    view = EvidencePlanUserViewPresenter().present(value, "SOURCE_PLAN")

    assert view.user_action_state == "VERIFY_DECLARED_PREREQUISITES"
    assert view.user_action == (
        "Vérifier explicitement les prérequis déclarés avant toute déclaration : "
        "documented_microphone_position, same_gain."
    )
    assert view.preparation_lines == (
        "Prérequis à confirmer : documented_microphone_position, same_gain",
        "Variables modifiées : active_channel",
        "Variables contrôlées : gain, microphone_position",
        "Mesures à réaliser : left_response, right_response",
        "Observations attendues : channel_difference",
        "Procédure 1 : Measure left.",
        "Procédure 2 : Measure right.",
        "Critères de réussite : Difference is repeatable.",
        "Critères d’échec : Gain changed.",
        "Limites scientifiques : Causality is not established.",
    )
    assert view.scientific_boundary_lines[-1] == (
        "READY signifie seulement que le contrat de préparation est complet ; "
        "les prérequis ne sont pas vérifiés et l’expérience n’est ni déclarée "
        "ni exécutée."
    )


def test_blocked_plan_never_exposes_an_execution_checklist():
    view = EvidencePlanUserViewPresenter().present(report(), "SOURCE_PLAN")
    assert view.preparation_lines == (
        "Préparation indisponible : le plan doit rester BLOCKED tant que son "
        "contrat n’est pas complet.",
    )


def test_overview_rejects_duplicate_plan_identity():
    value = report()
    value.evidence_acquisition_plans = SimpleNamespace(
        plans=value.evidence_acquisition_plans.plans * 2
    )
    with pytest.raises(ValueError, match="Ambiguous evidence plan_id"):
        EvidencePlanOverviewPresenter().present(value)


def test_empty_overview_is_explicit(capsys):
    value = SimpleNamespace(
        evidence_acquisition_plans=SimpleNamespace(plans=()),
        deterministic_evidence_weighting=SimpleNamespace(weights=()),
        deterministic_corrective_actions=SimpleNamespace(actions=()),
    )
    value.evidence_plan_overview = EvidencePlanOverviewPresenter().present(value)
    EvidencePlanOverviewConsoleReporter().print(value)
    output = capsys.readouterr().out
    assert "Aucun plan disponible." in output
    assert "Aucun plan n’est sélectionné ou recommandé" in output


def test_main_run_projects_overview_without_selecting_a_plan():
    value = report()
    calls = []
    brain = SimpleNamespace(analyze=lambda **arguments: (
        calls.append(arguments) or value
    ))
    reporter = SimpleNamespace(reports=[], print=lambda item: reporter.reports.append(item))

    result = acousticbrain_main.run(
        SimpleNamespace(resolve=lambda: "/measurements"),
        evidence_plan_overview=True,
        brain=brain,
        reporter=reporter,
    )

    assert calls[0]["synthesize_evidence_acquisition"] is True
    assert tuple(item.plan_id for item in result.evidence_plan_overview.plans) == (
        "SOURCE_PLAN",
    )
    assert reporter.reports == [result]
