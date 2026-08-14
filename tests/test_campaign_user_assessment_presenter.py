from dataclasses import FrozenInstanceError
import inspect

import pytest

import acousticbrain.report.campaign_user_assessment_presenter as presenter_module
from acousticbrain.brain import AcousticBrain
from acousticbrain.report import (
    CampaignUserAssessmentConsoleReporter,
    CampaignUserAssessmentPresenter,
    PresentedAnalysisReadiness,
    PresentedAnalysisReadinessReport,
    PresentedCorrectiveActionJustification,
    PresentedDeterministicAcousticReasoning,
    PresentedDeterministicAcousticReasoningReport,
    PresentedDeterministicCorrectiveAction,
    PresentedDeterministicCorrectiveActionReport,
    PresentedEvidenceAcquisitionPlan,
    PresentedEvidenceAcquisitionPlanReport,
    Report,
)


CONCLUSIONS = (
    ("ASYMMETRIC_SPEAKER_ROOM_INTERACTION_REASONING", "CONTRADICTORY_EVIDENCE"),
    ("MODAL_BASS_PERSISTENCE_REASONING", "NON_DISCRIMINATED"),
    ("DOMINANT_EARLY_REFLECTION_INTERACTION_REASONING", "SUPPORTED"),
    ("SBIR_PLACEMENT_INTERACTION_REASONING", "INSUFFICIENT_EVIDENCE"),
)


def reasoning(identifier, conclusion):
    return PresentedDeterministicAcousticReasoning(
        reasoning_id=identifier,
        category="HYPOTHESIS_EXPLANATION",
        title=f"Existing title for {identifier}",
        conclusion=conclusion,
        confidence=75.0,
        observation_ids=(f"OBSERVATION_{identifier}",),
        premises=(),
        inference_steps=(),
        supporting_evidence=(f"support.{identifier}",),
        contradicting_evidence=(
            (f"contradiction.{identifier}",)
            if conclusion == "CONTRADICTORY_EVIDENCE"
            else ()
        ),
        limitations=(f"limitation.{identifier}",),
        compatible_hypothesis_ids=(identifier.removesuffix("_REASONING"),),
        excluded_conclusions=("CAUSALITY_ESTABLISHED",),
        upstream_source_ids=("AcousticReasoningAnalysis",),
    )


def action(identifier, applicability, reasoning_id):
    return PresentedDeterministicCorrectiveAction(
        action_id=identifier,
        category="MEASUREMENT",
        action_type="RUN_CONTROLLED_MEASUREMENT",
        target_id=reasoning_id,
        title=f"Existing action {identifier}",
        objective="Existing objective.",
        description="Existing controlled measurement description.",
        applicability=applicability,
        priority="MEDIUM",
        confidence=70.0,
        source_reasoning_ids=(reasoning_id,),
        source_observation_ids=(f"OBSERVATION_{reasoning_id}",),
        upstream_source_ids=("AcousticReasoningAnalysis",),
        justifications=(
            PresentedCorrectiveActionJustification(
                justification_id=f"JUSTIFICATION_{identifier}",
                rule_id="MAP_BOUNDED_REASONING_TO_DECLARATIVE_ACTION_V1",
                reasoning_id=reasoning_id,
                conclusion_code="SUPPORTED",
                statement="Existing deterministic justification.",
            ),
        ),
        preconditions=("existing_precondition",),
        known_parameters=(),
        derivable_parameters=(),
        required_missing_parameters=(
            ("existing_missing_parameter",)
            if applicability == "BLOCKED_BY_MISSING_PARAMETERS"
            else ()
        ),
        forbidden_to_invent_parameters=("invented_setting",),
        known_risks=("existing_risk",),
        constraints=("existing_constraint",),
        success_criteria=("existing_success_criterion",),
        stop_criteria=("existing_stop_criterion",),
        contradictions=(
            ("existing_contradiction",)
            if applicability == "BLOCKED_BY_CONTRADICTION"
            else ()
        ),
        limitations=("No improvement is guaranteed.",),
        traceability_status="COMPLETE",
        compatible_protocol_ids=(),
        compatible_plan_ids=(),
    )


def selected_plan():
    return PresentedEvidenceAcquisitionPlan(
        plan_id=(
            "EVIDENCE_ACQUISITION_ASYMMETRIC_SPEAKER_ROOM_INTERACTION_"
            "REASONING_RESOLVE_CONTRADICTION"
        ),
        reasoning_id="ASYMMETRIC_SPEAKER_ROOM_INTERACTION_REASONING",
        corrective_action_id="ACTION_ASYMMETRY",
        evidence_weight_id="WEIGHT_ASYMMETRY",
        blocking_factor_ids=("contradictory_evidence.asymmetry",),
        objective="Acquire repeatable evidence for the existing contradiction.",
        test_type="CHANNEL_ISOLATION",
        instructions=("Existing instruction.",),
        required_inputs=(
            "documented_microphone_position",
            "existing_acquisition_settings",
        ),
        controlled_variables=("gain",),
        independent_variables=("active_channel",),
        measurements_to_capture=("left_channel_response",),
        expected_observations=("channel_specific_metric",),
        success_criteria=("Existing criterion.",),
        failure_criteria=("Existing failure criterion.",),
        resulting_evidence_targets=("ASYMMETRY",),
        priority="CRITICAL",
        estimated_effort="MEDIUM",
        status="READY",
        limitations=("The plan has not been executed.",),
    )


def exp_007_report():
    report = Report(project_name="exp-007-fixture")
    report.analysis_readiness = PresentedAnalysisReadinessReport(
        analyses=(
            PresentedAnalysisReadiness("FREQUENCY", "AVAILABLE"),
            PresentedAnalysisReadiness(
                "BASS_DECAY",
                "AVAILABLE_WITH_RESERVATIONS",
                reservation_issue_codes=("EXISTING_RESERVATION",),
            ),
        )
    )
    report.deterministic_acoustic_reasoning = (
        PresentedDeterministicAcousticReasoningReport(
            reasonings=tuple(reasoning(*values) for values in CONCLUSIONS)
        )
    )
    report.deterministic_corrective_actions = (
        PresentedDeterministicCorrectiveActionReport(
            actions=(
                action("ACTION_ASYMMETRY", "BLOCKED_BY_CONTRADICTION", CONCLUSIONS[0][0]),
                action("ACTION_MODAL", "CONDITIONALLY_APPLICABLE", CONCLUSIONS[1][0]),
                action("ACTION_EARLY", "APPLICABLE", CONCLUSIONS[2][0]),
                action("ACTION_SBIR", "BLOCKED_BY_MISSING_PARAMETERS", CONCLUSIONS[3][0]),
                action("ACTION_TESTED", "ALREADY_TESTED", CONCLUSIONS[2][0]),
                action("ACTION_NONE", "NO_ACTION_REQUIRED", CONCLUSIONS[2][0]),
            )
        )
    )
    report.evidence_acquisition_plans = PresentedEvidenceAcquisitionPlanReport(
        plans=(selected_plan(),)
    )
    return report


def test_exp_007_projection_preserves_v1_order_states_and_selected_plan():
    assessment = CampaignUserAssessmentPresenter().present(exp_007_report())

    assert tuple(
        (finding.reasoning_id, finding.conclusion)
        for finding in assessment.key_findings
    ) == CONCLUSIONS
    assert tuple(
        finding.reasoning_id
        for finding in assessment.uncertainties_and_contradictions
    ) == tuple(identifier for identifier, _ in CONCLUSIONS if identifier != CONCLUSIONS[2][0])
    assert tuple(
        value.action_id
        for value in assessment.currently_applicable_controlled_actions
    ) == ("ACTION_EARLY",)
    assert tuple(
        value.applicability for value in assessment.actions_not_yet_justified
    ) == (
        "BLOCKED_BY_CONTRADICTION",
        "CONDITIONALLY_APPLICABLE",
        "BLOCKED_BY_MISSING_PARAMETERS",
        "ALREADY_TESTED",
        "NO_ACTION_REQUIRED",
    )
    assert assessment.recommended_next_step is not None
    assert assessment.recommended_next_step.plan_id == selected_plan().plan_id
    assert assessment.prerequisites == selected_plan().required_inputs
    assert assessment.recommended_next_step.prerequisite_status == (
        "AVAILABILITY_NOT_VERIFIED"
    )


def test_projection_preserves_readiness_limitations_and_provenance():
    assessment = CampaignUserAssessmentPresenter().present(exp_007_report())

    assert tuple(
        (value.family, value.status)
        for value in assessment.measurement_status.analysis_readiness
    ) == (
        ("FREQUENCY", "AVAILABLE"),
        ("BASS_DECAY", "AVAILABLE_WITH_RESERVATIONS"),
    )
    finding = assessment.key_findings[0]
    assert finding.supporting_evidence == (f"support.{CONCLUSIONS[0][0]}",)
    assert finding.contradicting_evidence == (f"contradiction.{CONCLUSIONS[0][0]}",)
    assert finding.limitations == (f"limitation.{CONCLUSIONS[0][0]}",)
    assert finding.excluded_conclusions == ("CAUSALITY_ESTABLISHED",)
    assert ("REASONING", CONCLUSIONS[0][0]) in tuple(
        (source.source_type, source.source_id) for source in finding.provenance
    )


def test_absent_v1_recommendation_remains_none():
    report = exp_007_report()
    report.evidence_acquisition_plans = PresentedEvidenceAcquisitionPlanReport(plans=())

    assessment = CampaignUserAssessmentPresenter().present(report)

    assert assessment.recommended_next_step is None
    assert assessment.prerequisites == ()


def test_multi_experiment_report_projects_the_exact_v1_recommended_plan(
    historical_campaign_root,
):
    report = AcousticBrain().analyze(
        measurement_root=historical_campaign_root,
        compare_experiments=True,
        synthesize_evidence_acquisition=True,
    )
    selected_by_v1 = report.evidence_acquisition_plans.recommended_plan

    assert selected_by_v1 is not None
    assert selected_by_v1.status == "READY"
    projected = report.campaign_user_assessment.recommended_next_step
    assert projected is not None
    assert projected.plan_id == selected_by_v1.plan_id
    assert projected.required_inputs == selected_by_v1.required_inputs
    assert projected.prerequisite_status == selected_by_v1.prerequisite_status
    assert (
        "EVIDENCE_PLAN",
        selected_by_v1.plan_id,
    ) in tuple(
        (source.source_type, source.source_id)
        for source in projected.provenance
    )


def test_presented_assessment_is_immutable():
    assessment = CampaignUserAssessmentPresenter().present(exp_007_report())

    with pytest.raises(FrozenInstanceError):
        assessment.prerequisites = ()


def test_presenter_has_no_analysis_engine_or_llm_dependency():
    source = inspect.getsource(presenter_module)

    assert "acousticbrain.analysis" not in source
    assert "Advisor" not in source
    assert "LLM" not in source
    assert "_PRIORITY_ORDER" not in source
    assert "_EFFORT_ORDER" not in source


def test_console_is_stable_concise_and_preserves_scientific_boundaries(capsys):
    report = exp_007_report()
    report.campaign_user_assessment = CampaignUserAssessmentPresenter().present(report)
    renderer = CampaignUserAssessmentConsoleReporter()

    renderer.print(report)
    first = capsys.readouterr().out
    renderer.print(report)
    second = capsys.readouterr().out

    assert first == second
    assert "Currently applicable controlled actions" in first
    assert "Planning status: READY" in first
    assert "Confidence: 75.0 / 100" in first
    assert "Ready to execute" not in first
    assert "SUPPORTED does not establish causality." in first
    assert "APPLICABLE does not establish benefit or physical safety." in first
    assert "this will improve the room" not in first.casefold()
    assert "support.DOMINANT" not in first
    assert first.count("Limitation: limitation.ASYMMETRIC") == 1
    assert (
        "Inspect and prepare this existing plan with --guided-status before "
        "declaration or acquisition."
    ) in first
    assert "--full-assessment, --reasoning, --actions" in first
