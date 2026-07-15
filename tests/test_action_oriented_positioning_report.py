from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace

import pytest

from acousticbrain.diagnostics import Diagnostic
from acousticbrain.models import EvidenceLevel
from acousticbrain.report import (
    ActionOrientedPositioningPresenter,
    ConsoleReporter,
    PresentedControlledReflectionExperimentComparison,
    PresentedControlledReflectionHypothesisStatusUpdate,
    PresentedControlledReflectionVerificationPlanningAnalysis,
    PresentedExperimentCandidate,
    PresentedExperimentPlanning,
    PresentedReflectionCandidateVerificationProposal,
    Report,
)
from acousticbrain.report.prioritizer import DiagnosticPriorityAnalyzer


def candidate(
    *,
    parameters=None,
    changed=("LOUDSPEAKER_POSITION",),
    controlled=(
        "MICROPHONE_POSITION",
        "MEASUREMENT_LEVEL",
        "LOUDSPEAKER_ORIENTATION",
        "OTHER_LOUDSPEAKER_POSITIONS",
    ),
):
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
        observable_fact_codes=(
            "sbir.predicted_cancellation_frequency_hz",
            "SBIR_MOVES_WITH_SPEAKER",
        ),
        prerequisite_codes=(),
        unmet_prerequisite_codes=(),
        primary_selection_reason="DISCRIMINATES_HYPOTHESES",
        eligible=True,
        ineligibility_reasons=(),
        parameters=parameters or {},
        controlled_variable_codes=controlled,
        changed_variable_codes=changed,
    )


def planning(item):
    return PresentedExperimentPlanning(
        status="READY",
        recommended_candidate=item,
        alternatives=(),
        all_candidates=(item,),
        applied_rule_codes=("PLAN_DETERMINISTIC_ORDER_V1",),
        technical_confidence=80.0,
        source_analysis_codes=("ExperimentPlanningAnalysis",),
        uncovered_active_action_codes=(),
    )


def proposal(suffix="front"):
    return PresentedReflectionCandidateVerificationProposal(
        proposal_id=f"reflection_verification_proposal.{suffix}",
        source_candidate_id=f"material_reflection_candidate.{suffix}",
        proposal_order=1,
        correlation_id=f"correlation.{suffix}",
        path_id=f"path.{suffix}",
        surface_id=f"surface.{suffix}",
        region_id=None,
        observed_event_id=f"event.{suffix}",
        target_kind="SURFACE",
        target_id=f"surface.{suffix}",
        method="TEMPORARY_MASK",
        reference_condition_code="UNMASKED_REFERENCE",
        intervention_condition_code="TEMPORARY_MASK_APPLIED",
        controlled_variable_codes=(
            "MICROPHONE_POSITION",
            "LOUDSPEAKER_POSITION",
            "LOUDSPEAKER_ORIENTATION",
            "MEASUREMENT_LEVEL",
        ),
        changed_variable_codes=("TEMPORARY_MASK_STATE",),
        observable_fact_codes=(
            "etc.observed_event_delay_ms",
            "etc.observed_event_relative_level_db",
        ),
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


def comparison(status):
    return PresentedControlledReflectionExperimentComparison(
        comparison_id="reflection_comparison.test",
        experiment_declaration_id="reflection_declaration.test",
        proposal_id="reflection_verification_proposal.front",
        status=status,
        temporal_window_code="event.front",
        baseline_measurement_reference_ids=("reference.before",),
        intervention_measurement_reference_ids=("reference.after",),
        observed_differences=(),
        reason_codes=("SYNTHETIC_TEST",),
        causality_status="NOT_ESTABLISHED",
        ranking_impact="NONE",
        recommendation_impact="NONE",
        eligibility_impact="NONE",
        source_analysis_codes=("ControlledReflectionExperimentComparison",),
        applied_rule_codes=("COMPARE_DECLARED_OBSERVABLES_ONLY",),
    )


def update(status):
    return PresentedControlledReflectionHypothesisStatusUpdate(
        update_id="reflection_hypothesis_status_update.test",
        target_kind="CANDIDATE",
        target_id="material_reflection_candidate.front",
        proposal_id="reflection_verification_proposal.front",
        experiment_declaration_id="reflection_declaration.test",
        comparison_id="reflection_comparison.test",
        status=status,
        measured_fact_codes=("etc.observed_event_relative_level_db",),
        comparison_result_codes=("CHANGE_OBSERVED",),
        transition_rule_codes=("OBSERVATION_SUPPORT_ONLY",),
        status_provenance_codes=("PR-039",),
        justification_codes=("SYNTHETIC_TEST",),
        causality_status="NOT_ESTABLISHED",
        recommendation_impact="NONE",
        ranking_impact="NONE",
        eligibility_impact="NONE",
        source_analysis_codes=("ControlledReflectionHypothesisStatusUpdate",),
    )


def diagnostic(title="Symétrie stéréo", confidence=90):
    return Diagnostic(
        title=title,
        message="Une asymétrie mesurée reste à vérifier.",
        severity="HIGH",
        confidence=confidence,
        evidence_level=EvidenceLevel.OBSERVED,
        observations=["Écart G-D médium : +2,1 dB."],
        conclusion="Une asymétrie mesurée reste à vérifier.",
        causes=["Placement", "Interaction avec la pièce"],
    )


def report_with_priority(*diagnostics):
    report = Report(project_name="fixture")
    report.diagnostics = list(diagnostics or (diagnostic(),))
    report.diagnostic_priority = DiagnosticPriorityAnalyzer().analyze(
        report.diagnostics
    )
    return report


def rendered(report):
    stream = StringIO()
    with redirect_stdout(stream):
        ConsoleReporter().print(report)
    return stream.getvalue()


def test_presents_an_existing_positioning_proposal_as_a_controlled_test():
    report = report_with_priority()
    report.experiment_planning = planning(candidate(parameters={
        "speaker_id": "LEFT",
        "proposed_displacement_m": 0.10,
        "movement_direction": "vers l’avant",
    }))

    result = ActionOrientedPositioningPresenter().present(report)

    assert result.status == "ACTION_AVAILABLE"
    assert result.target == "l’enceinte gauche"
    assert result.direction == "vers l’avant"
    assert result.amplitude == "10 cm"
    assert result.required_measurements == ("L", "R", "L+R")
    assert "la position du microphone" in result.unchanged_items
    assert "la position de l’autre enceinte" in result.unchanged_items


def test_reports_insufficient_data_without_a_proposal():
    result = ActionOrientedPositioningPresenter().present(report_with_priority())

    assert result.status == "INSUFFICIENT_DATA"
    assert "Aucune expérience de positionnement fiable" in result.action
    assert result.target is None


def test_pr036_proposal_alone_does_not_become_a_recommendation():
    report = report_with_priority()
    report.controlled_reflection_verification_planning = (
        PresentedControlledReflectionVerificationPlanningAnalysis(
            proposals=(proposal(),),
            exclusions=(),
            source_analysis_codes=("MaterialAwareReflectionCandidateAnalysis",),
            applied_rule_codes=("REFLECTION_VERIFICATION_EXISTING_CANDIDATES_ONLY",),
        )
    )

    result = ActionOrientedPositioningPresenter().present(report)

    assert result.status == "INSUFFICIENT_DATA"
    assert "déclaration d’expérience planifiée" in result.missing_information[0]


def test_presents_an_existing_planned_reflection_experiment():
    report = report_with_priority()
    item = proposal()
    report.controlled_reflection_verification_planning = (
        PresentedControlledReflectionVerificationPlanningAnalysis(
            proposals=(item,),
            exclusions=(),
            source_analysis_codes=("MaterialAwareReflectionCandidateAnalysis",),
            applied_rule_codes=("REFLECTION_VERIFICATION_EXISTING_CANDIDATES_ONLY",),
        )
    )
    report.controlled_reflection_experiment_declarations = (
        SimpleNamespace(status="PLANNED", proposal_id=item.proposal_id),
    )

    result = ActionOrientedPositioningPresenter().present(report)

    assert result.status == "ACTION_AVAILABLE"
    assert result.target == "la surface surface.front"
    assert "masquage temporaire" in result.action


def test_reports_multiple_equally_prioritized_paths_without_choosing_one():
    report = report_with_priority(
        diagnostic("Symétrie stéréo"),
        diagnostic("Réflexions temporelles précoces"),
    )

    result = ActionOrientedPositioningPresenter().present(report)

    assert result.status == "MULTIPLE_PLAUSIBLE_PATHS"
    assert "Plusieurs explications restent également plausibles" in result.action
    assert result.target is None


@pytest.mark.parametrize(
    ("status", "expected"),
    (
        ("NOT_COMPARABLE", "ne permettent pas de comparer"),
        ("INCONCLUSIVE", "résultat suffisamment clair"),
        ("NO_OBSERVABLE_CHANGE", "Aucun changement mesurable"),
        ("CHANGE_OBSERVED", "Un changement mesurable"),
    ),
)
def test_translates_existing_comparison_results_without_claiming_improvement(
    status,
    expected,
):
    report = report_with_priority()
    report.controlled_reflection_experiment_comparisons = (comparison(status),)

    result = ActionOrientedPositioningPresenter().present(report)

    assert expected in result.previous_result
    assert "amélioration" not in result.previous_result.lower()


@pytest.mark.parametrize(
    ("status", "expected"),
    (
        ("SUPPORTED_BY_OBSERVATION", "soutient la piste"),
        ("NOT_SUPPORTED_BY_OBSERVATION", "ne soutient pas la piste"),
    ),
)
def test_translates_observation_support_without_establishing_causality(
    status,
    expected,
):
    report = report_with_priority()
    report.controlled_reflection_hypothesis_status_updates = (update(status),)

    result = ActionOrientedPositioningPresenter().present(report)

    assert expected in result.previous_result
    assert result.causality_status == "NOT_ESTABLISHED"


def test_missing_direction_and_distance_remain_explicitly_absent():
    report = report_with_priority()
    report.experiment_planning = planning(candidate(parameters={"speaker_id": "LEFT"}))

    result = ActionOrientedPositioningPresenter().present(report)

    assert result.status == "ACTION_AVAILABLE"
    assert result.direction is None
    assert result.amplitude is None


def test_renderer_does_not_invent_direction_or_distance():
    report = report_with_priority()
    report.experiment_planning = planning(candidate(parameters={"speaker_id": "LEFT"}))

    output = rendered(report)

    assert "Direction : non déterminée par les données disponibles" in output
    assert "Amplitude : non déterminée par les données disponibles" in output
    assert "vers l’intérieur" not in output
    assert "vers l’extérieur" not in output
    assert " cm" not in output


def test_preserves_not_established_in_user_summary():
    report = report_with_priority()
    report.controlled_reflection_verification_planning = (
        PresentedControlledReflectionVerificationPlanningAnalysis(
            proposals=(proposal(),),
            exclusions=(),
            source_analysis_codes=("MaterialAwareReflectionCandidateAnalysis",),
            applied_rule_codes=("REFLECTION_VERIFICATION_EXISTING_CANDIDATES_ONLY",),
        )
    )

    result = ActionOrientedPositioningPresenter().present(report)

    assert result.causality_status == "NOT_ESTABLISHED"
    assert "Statut scientifique conservé : NOT_ESTABLISHED" in rendered(report)


def test_keeps_pr036_to_pr039_technical_details_after_user_summary():
    report = report_with_priority()
    report.controlled_reflection_verification_planning = (
        PresentedControlledReflectionVerificationPlanningAnalysis(
            proposals=(proposal(),),
            exclusions=(),
            source_analysis_codes=("MaterialAwareReflectionCandidateAnalysis",),
            applied_rule_codes=("REFLECTION_VERIFICATION_EXISTING_CANDIDATES_ONLY",),
        )
    )
    report.controlled_reflection_experiment_comparisons = (
        comparison("CHANGE_OBSERVED"),
    )
    report.controlled_reflection_hypothesis_status_updates = (
        update("SUPPORTED_BY_OBSERVATION"),
    )

    output = rendered(report)

    assert "PROCHAINE ÉTAPE DE POSITIONNEMENT" in output
    assert "Controlled reflection verification proposals" in output
    assert "Deterministic reflection experiment comparisons" in output
    assert "Controlled reflection hypothesis observation status" in output
    assert "Causality: NOT_ESTABLISHED" in output


def test_user_summary_precedes_all_technical_details():
    report = report_with_priority()
    report.controlled_reflection_verification_planning = (
        PresentedControlledReflectionVerificationPlanningAnalysis(
            proposals=(proposal(),),
            exclusions=(),
            source_analysis_codes=("MaterialAwareReflectionCandidateAnalysis",),
            applied_rule_codes=("REFLECTION_VERIFICATION_EXISTING_CANDIDATES_ONLY",),
        )
    )

    output = rendered(report)

    assert output.index("PROCHAINE ÉTAPE DE POSITIONNEMENT") < output.index(
        "Controlled reflection verification proposals"
    )
    assert output.index("PROCHAINE ÉTAPE DE POSITIONNEMENT") < output.index(
        "Symétrie stéréo"
    )


def test_rendering_is_deterministic_when_repeated():
    report = report_with_priority()
    report.experiment_planning = planning(candidate(parameters={
        "speaker_id": "LEFT",
        "proposed_displacement_m": 0.05,
    }))

    assert rendered(report) == rendered(report)


def test_reference_shaped_plan_without_positioning_variables_is_honest():
    report = report_with_priority(diagnostic("Modes propres", confidence=99))
    report.experiment_planning = planning(candidate(
        parameters={},
        changed=(),
        controlled=(),
    ))

    output = rendered(report)

    assert "Aucune expérience de positionnement fiable" in output
    assert "Données encore nécessaires" in output
    assert "Action proposée\nDéplacez" not in output


def test_user_summary_contains_no_unsupported_causal_or_optimality_claims():
    report = report_with_priority()
    report.experiment_planning = planning(candidate(parameters={
        "speaker_id": "RIGHT",
        "proposed_displacement_m": 0.05,
    }))
    output = rendered(report).lower()

    for forbidden in (
        "cause confirmée",
        "position optimale",
        "amélioration garantie",
        "ce mur provoque",
    ):
        assert forbidden not in output
