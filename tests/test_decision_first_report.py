from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace

import pytest

from acousticbrain.diagnostics import Diagnostic
from acousticbrain.models import (
    EvidenceLevel,
    RecommendationPriority,
    RecommendationStatus,
)
from acousticbrain.report import (
    ConsoleReporter,
    DecisionFirstReportPresenter,
    PresentedControlledReflectionVerificationPlanningAnalysis,
    PresentedExperimentCandidate,
    PresentedExperimentComparison,
    PresentedExperimentEvolution,
    PresentedExperimentPlanning,
    PresentedRecommendation,
    PresentedReflectionCandidateVerificationProposal,
    Report,
)
from acousticbrain.report.prioritizer import DiagnosticPriorityAnalyzer


def evolution(
    acoustic_outcome="MIXED",
    *,
    outcome="INCONCLUSIVE",
    eligibility="COMPARABLE",
    protocol="protocol.test.v1",
    hypothesis="HYPOTHESIS_TEST",
    observations=(),
):
    return PresentedExperimentEvolution(
        before_experiment_id="exp-005",
        after_experiment_id="exp-006",
        comparison_type="LOCAL",
        eligibility=eligibility,
        ineligibility_reasons=(),
        source_protocol_id=protocol,
        source_hypothesis_code=hypothesis,
        experiment_parameters=(),
        outcome=outcome,
        acoustic_outcome=acoustic_outcome,
        experimental_result_labels=(),
        improved_fact_codes=(),
        degraded_fact_codes=(),
        changed_fact_codes=(),
        unchanged_fact_codes=(),
        unavailable_fact_codes=(),
        observation_labels=tuple(observations),
        counter_fact_codes=(),
        unresolved_discrimination_labels=(),
        technical_confidence=80.0,
        trace_id="comparison.local.exp-005.exp-006",
        trace_before_file_hash="before",
        trace_after_file_hash="after",
        trace_before_fact_codes=(),
        trace_after_fact_codes=(),
        trace_delta_fact_codes=(),
        trace_observed_fact_codes=(),
        trace_unresolved_discrimination_codes=(),
    )


def with_comparison(report, item):
    report.experiment_comparison = PresentedExperimentComparison(
        chronology=(item.before_experiment_id, item.after_experiment_id),
        local_comparisons=(item,),
        cumulative_comparisons=(),
        detailed_traceability=False,
    )
    return report


def candidate(parameters=None):
    return PresentedExperimentCandidate(
        candidate_id="experiment_candidate.sbir_placement_interaction",
        source_protocol_id="protocol.temporary_move_speaker.v1",
        hypothesis_code="SBIR_PLACEMENT_INTERACTION",
        source_action_code="VERIFY_SBIR_PLACEMENT",
        informative_value=82.0,
        difficulty="MEDIUM",
        reversibility="HIGH",
        estimated_duration_minutes=30,
        cost_category="LOW",
        objective_code="DISCRIMINATE_SBIR_PLACEMENT_INTERACTION",
        observable_fact_codes=("SBIR_MOVES_WITH_SPEAKER",),
        prerequisite_codes=(),
        unmet_prerequisite_codes=(),
        primary_selection_reason="DISCRIMINATES_HYPOTHESES",
        eligible=True,
        ineligibility_reasons=(),
        parameters=parameters or {},
        controlled_variable_codes=(
            "MICROPHONE_POSITION",
            "MEASUREMENT_LEVEL",
            "OTHER_LOUDSPEAKER_POSITIONS",
            "ROOM_CONFIGURATION",
        ),
        changed_variable_codes=("LOUDSPEAKER_POSITION",),
    )


def planning(item=None, *, status="READY", all_candidates=()):
    return PresentedExperimentPlanning(
        status=status,
        recommended_candidate=item,
        alternatives=(),
        all_candidates=tuple(all_candidates),
        applied_rule_codes=("PLAN_DETERMINISTIC_ORDER_V1",),
        technical_confidence=80.0,
        source_analysis_codes=("ExperimentPlanningAnalysis",),
        uncovered_active_action_codes=(),
    )


def recommendation(code, priority=RecommendationPriority.HIGH, status=None):
    return PresentedRecommendation(
        code=code,
        action="investigate",
        target="target",
        priority=priority,
        confidence=80.0,
        source_analyses=("SyntheticAnalysis",),
        status=status or RecommendationStatus.ACTIVE,
    )


def proposal():
    return PresentedReflectionCandidateVerificationProposal(
        proposal_id="reflection_verification_proposal.front",
        source_candidate_id="material_reflection_candidate.front",
        proposal_order=1,
        correlation_id="correlation.front",
        path_id="path.front",
        surface_id="surface.front",
        region_id=None,
        observed_event_id="event.front",
        target_kind="SURFACE",
        target_id="surface.front",
        method="TEMPORARY_MASK",
        reference_condition_code="UNMASKED_REFERENCE",
        intervention_condition_code="TEMPORARY_MASK_APPLIED",
        controlled_variable_codes=(
            "MICROPHONE_POSITION",
            "LOUDSPEAKER_POSITION",
            "MEASUREMENT_LEVEL",
        ),
        changed_variable_codes=("TEMPORARY_MASK_STATE",),
        observable_fact_codes=("etc.observed_event_relative_level_db",),
        supporting_outcome_codes=("REFLECTION_DECREASES_AFTER_MASKING",),
        counter_outcome_codes=("REFLECTION_REMAINS_UNCHANGED_AFTER_MASKING",),
        source_evidence_codes=("evidence.reflection",),
        source_provenance_codes=("PR-035",),
        planning_rule_codes=("REFLECTION_VERIFICATION_EXISTING_CANDIDATES_ONLY",),
        execution_status="NOT_EXECUTED",
        causality_status="NOT_ESTABLISHED",
        eligibility_impact="NONE",
        recommendation_impact="NONE",
        limitations=("CAUSALITY_NOT_ESTABLISHED",),
    )


def report():
    return Report(project_name="fixture")


def rendered(value):
    stream = StringIO()
    with redirect_stdout(stream):
        ConsoleReporter().print(value)
    return stream.getvalue()


def rendered_decision(value):
    stream = StringIO()
    decision = DecisionFirstReportPresenter().present(value)
    with redirect_stdout(stream):
        ConsoleReporter._print_decision_first(decision)
    return stream.getvalue()


def decision_section(output):
    return output.split("DÉCISION ACOUSTIQUE\n", 1)[1].split(
        "\nPROCHAINE ÉTAPE DE POSITIONNEMENT",
        1,
    )[0]


@pytest.mark.parametrize(
    ("status", "expected"),
    (
        ("IMPROVED", "amélioration mesurable"),
        ("DEGRADED", "dégradation mesurable"),
        ("MIXED", "améliorations et des dégradations"),
        ("UNCHANGED", "Aucun changement acoustique significatif"),
        ("INCONCLUSIVE", "ne permettent pas de conclure"),
    ),
)
def test_translates_last_experiment_verdict_without_recalculating_it(status, expected):
    value = with_comparison(report(), evolution(status))

    decision = DecisionFirstReportPresenter().present(value)

    assert expected in decision.verdict
    assert decision.comparison_context[0] == "Comparaison : exp-005 → exp-006."
    assert "périmètre mesuré" in decision.comparison_context[-1]


def test_not_comparable_experiment_has_no_reliable_verdict():
    value = with_comparison(
        report(),
        evolution("IMPROVED", eligibility="NOT_COMPARABLE"),
    )

    decision = DecisionFirstReportPresenter().present(value)

    assert "ne peut pas être comparée" in decision.verdict
    assert decision.verdict_confidence == "Non établi"


def test_absent_comparison_is_reported_explicitly():
    decision = DecisionFirstReportPresenter().present(report())

    assert "ne peut pas être comparée" in decision.verdict
    assert decision.comparison_context == (
        "Aucune comparaison d’expérience n’est disponible.",
    )


def test_unique_eligible_action_is_presented_with_existing_operational_details():
    value = with_comparison(report(), evolution("MIXED"))
    value.experiment_planning = planning(candidate({
        "speaker_id": "LEFT",
        "movement_direction": "vers l’avant",
        "proposed_displacement_m": 0.10,
    }))

    decision = DecisionFirstReportPresenter().present(value)

    assert decision.action_status == "AVAILABLE"
    assert decision.target == "l’enceinte gauche"
    assert decision.direction == "vers l’avant"
    assert decision.amplitude == "10 cm"
    assert decision.required_measurements == ("L", "R", "L+R")
    assert "la position de l’autre enceinte" in decision.unchanged_items


def test_declared_planned_action_precedes_an_eligible_candidate():
    value = report()
    item = proposal()
    value.controlled_reflection_verification_planning = (
        PresentedControlledReflectionVerificationPlanningAnalysis(
            proposals=(item,),
            exclusions=(),
            source_analysis_codes=("PR-036",),
            applied_rule_codes=("STABLE_PROPOSAL_ORDER",),
        )
    )
    value.controlled_reflection_experiment_declarations = (
        SimpleNamespace(status="PLANNED", proposal_id=item.proposal_id),
    )
    value.experiment_planning = planning(candidate({"speaker_id": "LEFT"}))

    decision = DecisionFirstReportPresenter().present(value)

    assert decision.target == "la surface surface.front"
    assert "masquage temporaire" in decision.action


def test_equally_prioritized_active_actions_are_not_arbitrarily_selected():
    value = report()
    value.recommendations = [
        recommendation("CHECK_STEREO_PLACEMENT"),
        recommendation("INVESTIGATE_DOMINANT_EARLY_REFLECTIONS"),
    ]

    decision = DecisionFirstReportPresenter().present(value)

    assert decision.action_status == "TIED"
    assert "Plusieurs actions restent également prioritaires" in decision.action
    assert decision.target is None


def test_deferred_action_is_not_reactivated():
    value = report()
    value.recommendations = [
        recommendation(
            "VERIFY_SPEAKER_ROOM_ASYMMETRY",
            status=RecommendationStatus.DEFERRED,
        )
    ]
    value.causal_discrimination = SimpleNamespace(discrimination_decisions=(
        SimpleNamespace(status="DEFERRED"),
    ))

    decision = DecisionFirstReportPresenter().present(value)

    assert decision.action_status == "UNAVAILABLE"
    assert any("différée par décision utilisateur" in item for item in decision.action_reasons)
    assert any("décider de reprendre" in item for item in decision.unblock_steps)


@pytest.mark.parametrize(
    ("protocol", "hypothesis"),
    ((None, "HYPOTHESIS_TEST"), ("protocol.test.v1", None), (None, None)),
)
def test_missing_protocol_or_hypothesis_marks_the_change_as_undeclared(
    protocol,
    hypothesis,
):
    value = with_comparison(
        report(),
        evolution("MIXED", protocol=protocol, hypothesis=hypothesis),
    )

    decision = DecisionFirstReportPresenter().present(value)

    assert any("n’a pas été déclarée" in item for item in decision.action_reasons)
    assert any("ne sait pas précisément" in item for item in decision.active_limits)


def test_missing_direction_and_distance_are_not_invented():
    value = report()
    value.experiment_planning = planning(candidate({"speaker_id": "RIGHT"}))

    decision = DecisionFirstReportPresenter().present(value)
    output = rendered(value)

    assert decision.direction is None
    assert decision.amplitude is None
    assert "Direction :" not in decision_section(output)
    assert "Amplitude :" not in decision_section(output)


def test_complete_absence_of_action_does_not_request_a_new_measurement():
    decision = DecisionFirstReportPresenter().present(report())

    assert decision.action_status == "UNAVAILABLE"
    assert "Aucun déplacement fiable" in decision.action
    assert decision.required_measurements == ()


def test_page_limits_facts_and_active_limits_to_three():
    value = with_comparison(
        report(),
        evolution(
            "MIXED",
            protocol=None,
            hypothesis=None,
            observations=("fait 1", "fait 2", "fait 3", "fait 4"),
        ),
    )
    value.causal_discrimination = SimpleNamespace(discrimination_decisions=(
        SimpleNamespace(status="DEFERRED"),
    ))

    decision = DecisionFirstReportPresenter().present(value)

    assert decision.established_facts == ("fait 1", "fait 2", "fait 3")
    assert len(decision.active_limits) + 1 <= 3


def test_hypothesis_is_not_relabelled_as_an_established_fact():
    value = report()
    value.diagnostics = [Diagnostic(
        title="Hypothèse synthétique",
        message="Une explication reste possible.",
        severity="HIGH",
        confidence=80,
        evidence_level=EvidenceLevel.HYPOTHESIS,
        observations=["La surface avant pourrait être impliquée."],
    )]
    value.diagnostic_priority = DiagnosticPriorityAnalyzer().analyze(
        value.diagnostics
    )

    decision = DecisionFirstReportPresenter().present(value)

    assert decision.established_facts == ()


def test_preserves_not_established_explicitly():
    value = with_comparison(report(), evolution("IMPROVED"))

    decision = DecisionFirstReportPresenter().present(value)

    assert decision.causality_status == "NOT_ESTABLISHED"
    assert "Causalité : Non établi (NOT_ESTABLISHED)" in rendered(value)


def test_rendering_order_is_stable_and_decision_precedes_pr040_and_details():
    value = with_comparison(report(), evolution("MIXED"))
    value.room_properties = SimpleNamespace(
        volume=80.0,
        floor_area=30.0,
        schroeder_frequency=120.0,
    )

    output = rendered(value)

    assert output.index("DÉCISION ACOUSTIQUE") < output.index(
        "PROCHAINE ÉTAPE DE POSITIONNEMENT"
    )
    assert output.index("DÉCISION ACOUSTIQUE") < output.index("Salle")


def test_rendering_is_deterministic_when_repeated():
    value = with_comparison(report(), evolution("MIXED"))

    assert rendered(value) == rendered(value)


def test_decision_is_visible_in_first_thirty_useful_lines():
    output = rendered(with_comparison(report(), evolution("MIXED")))
    useful = [line for line in output.splitlines() if line.strip()]

    assert useful.index("DÉCISION ACOUSTIQUE") < 5
    assert useful.index("Verdict") < 30
    assert useful.index("Prochaine action") < 30


def test_decision_page_does_not_exceed_forty_five_lines_in_complex_case():
    value = with_comparison(
        report(),
        evolution(
            "MIXED",
            protocol=None,
            hypothesis=None,
            observations=("fait 1", "fait 2", "fait 3"),
        ),
    )
    value.experiment_planning = planning(candidate({
        "speaker_id": "LEFT",
        "movement_direction": "vers l’avant",
        "proposed_displacement_m": 0.10,
    }))

    lines = decision_section(rendered(value)).splitlines()

    assert len(lines) <= 45


def test_pr040_and_technical_details_remain_after_decision_page():
    value = report()
    value.recommendations = [recommendation("CHECK_STEREO_PLACEMENT")]

    output = rendered(value)

    assert "PROCHAINE ÉTAPE DE POSITIONNEMENT" in output
    assert "Recommandations structurées" in output
    assert "CHECK_STEREO_PLACEMENT" in output


def test_exp006_analogue_is_honest_and_actionable_without_inventing_a_move():
    value = with_comparison(
        report(),
        evolution("MIXED", protocol=None, hypothesis=None),
    )
    value.experiment_planning = planning(None, status="NO_ELIGIBLE_CANDIDATE")
    value.recommendations = [
        recommendation("CHECK_STEREO_PLACEMENT"),
        recommendation("INVESTIGATE_DOMINANT_EARLY_REFLECTIONS"),
    ]
    value.causal_discrimination = SimpleNamespace(discrimination_decisions=(
        SimpleNamespace(status="DEFERRED"),
    ))

    output = rendered_decision(value)

    assert "améliorations et des dégradations" in output
    assert "Aucun verdict global simple" in output
    assert "modification de la dernière expérience n’a pas été déclarée" in output
    assert "Aucune expérience contrôlée n’est actuellement éligible" in output
    assert "décider de reprendre" in output
    assert "Déclarez précisément ce qui a été modifié" in output
    assert "déplacez" not in output.lower()


def test_user_page_contains_no_unsupported_claim():
    value = with_comparison(report(), evolution("MIXED"))
    output = decision_section(rendered(value)).lower()

    for forbidden in (
        "position optimale",
        "amélioration garantie",
        "cause confirmée",
        "la nouvelle position est meilleure",
    ):
        assert forbidden not in output
