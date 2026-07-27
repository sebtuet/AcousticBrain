from copy import deepcopy

from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.models import Measurement
from acousticbrain.report import (
    AssessmentSummaryConsoleReporter,
    AssessmentSummaryPresenter,
    PresentedAcousticObservation,
    PresentedAcousticObservationReport,
    PresentedAnalysisReadiness,
    PresentedAnalysisReadinessReport,
    PresentedCorrectiveActionJustification,
    PresentedDeterministicCorrectiveAction,
    PresentedDeterministicCorrectiveActionReport,
    PresentedDiscoveredExperiment,
    PresentedEvidenceAcquisitionPlan,
    PresentedEvidenceAcquisitionPlanReport,
    PresentedExperimentDiscovery,
    Report,
)


class Project:
    name = "fixture"


def observation(identifier, title, description):
    return PresentedAcousticObservation(
        observation_id=identifier,
        category="FACT",
        title=title,
        description=description,
        confidence=90.0,
        supporting_evidence=("evidence",),
        contradicting_evidence=(),
        limitations=(),
        source_analysis_ids=("analysis",),
    )


def action(identifier, applicability):
    return PresentedDeterministicCorrectiveAction(
        action_id=identifier,
        category="MEASUREMENT",
        action_type="RUN_CONTROLLED_MEASUREMENT",
        target_id=f"TARGET-{identifier}",
        title=f"Title {identifier}",
        objective=f"Objective {identifier}",
        description=f"Description {identifier}",
        applicability=applicability,
        priority="MEDIUM",
        confidence=80.0,
        source_reasoning_ids=("REASONING-1",),
        source_observation_ids=("OBSERVATION-1",),
        upstream_source_ids=("ANALYSIS-1",),
        justifications=(
            PresentedCorrectiveActionJustification(
                justification_id=f"JUSTIFICATION-{identifier}",
                rule_id="ACTION-RULE-1",
                reasoning_id="REASONING-1",
                conclusion_code="CONCLUSION-1",
                statement="Existing action justification.",
            ),
        ),
        preconditions=(),
        known_parameters=(),
        derivable_parameters=(),
        required_missing_parameters=(),
        forbidden_to_invent_parameters=(),
        known_risks=(),
        constraints=(),
        success_criteria=(),
        stop_criteria=(),
        contradictions=(),
        limitations=(),
        traceability_status="COMPLETE",
        compatible_protocol_ids=(),
        compatible_plan_ids=(),
    )


def plan(identifier, status):
    return PresentedEvidenceAcquisitionPlan(
        plan_id=identifier,
        reasoning_id="REASONING-1",
        corrective_action_id="ACTION-1",
        evidence_weight_id="WEIGHT-1",
        blocking_factor_ids=("BLOCKING-1",),
        objective=f"Objective {identifier}",
        test_type="REPEAT_MEASUREMENT",
        instructions=("Existing instruction.",),
        required_inputs=(),
        controlled_variables=(),
        independent_variables=(),
        measurements_to_capture=(),
        expected_observations=(),
        success_criteria=("Existing criterion.",),
        failure_criteria=(),
        resulting_evidence_targets=("TARGET-1",),
        priority="MEDIUM",
        estimated_effort="LOW",
        status=status,
        limitations=(),
    )


def source_report():
    report = Report(project_name="fixture")
    report.experiments_discovered = PresentedExperimentDiscovery(
        experiments=(
            PresentedDiscoveredExperiment(
                experiment_id="baseline",
                experiment_type="BASELINE",
                state="READY",
                file_count=3,
                timestamp="ignored",
                available_channels=("LEFT", "RIGHT", "STEREO"),
            ),
            PresentedDiscoveredExperiment(
                experiment_id="exp-001",
                experiment_type="EXPERIMENT",
                state="INCOMPLETE",
                file_count=1,
                timestamp="ignored",
                available_channels=("LEFT",),
            ),
        )
    )
    report.analysis_readiness = PresentedAnalysisReadinessReport(
        analyses=tuple(
            PresentedAnalysisReadiness(family=family, status=status)
            for family, status in (
                ("FREQUENCY", "AVAILABLE"),
                ("RT60", "AVAILABLE_WITH_RESERVATIONS"),
                ("ETC", "AVAILABLE"),
                ("CLARITY", "BLOCKED"),
                ("SPATIAL", "BLOCKED"),
                ("DIRECT_REVERBERANT", "AVAILABLE"),
                ("BASS_DECAY", "AVAILABLE_WITH_RESERVATIONS"),
            )
        )
    )
    report.acoustic_observations = PresentedAcousticObservationReport(
        observations=(
            observation("OBSERVATION-1", "First finding", "First description."),
            observation("OBSERVATION-2", "Second finding", "Second description."),
        )
    )
    report.deterministic_corrective_actions = (
        PresentedDeterministicCorrectiveActionReport(
            actions=(
                action("ACTION-1", "APPLICABLE"),
                action("ACTION-2", "CONDITIONALLY_APPLICABLE"),
                action("ACTION-3", "BLOCKED_BY_CONTRADICTION"),
                action("ACTION-4", "NOT_SUPPORTED"),
                action("ACTION-5", "ALREADY_TESTED"),
            )
        )
    )
    report.evidence_acquisition_plans = PresentedEvidenceAcquisitionPlanReport(
        plans=(
            plan("PLAN-1", "READY"),
            plan("PLAN-2", "BLOCKED"),
        )
    )
    return report


def summarized_report():
    report = source_report()
    report.assessment_summary = AssessmentSummaryPresenter().present(report)
    return report


def render(report, capsys):
    AssessmentSummaryConsoleReporter().print(report)
    return capsys.readouterr().out


def test_presenter_uses_report_collections_without_reordering_or_rewriting():
    summary = AssessmentSummaryPresenter().present(source_report())

    assert tuple(item.experiment_id for item in summary.experiments) == (
        "baseline",
        "exp-001",
    )
    assert tuple(item.finding_id for item in summary.findings) == (
        "OBSERVATION-1",
        "OBSERVATION-2",
    )
    assert tuple(item.title for item in summary.findings) == (
        "First finding",
        "Second finding",
    )
    assert tuple(item.action_id for item in summary.applicable_actions) == (
        "ACTION-1",
        "ACTION-2",
    )
    assert tuple(item.action_id for item in summary.blocked_actions) == (
        "ACTION-3",
        "ACTION-4",
    )
    assert tuple(item.plan_id for item in summary.recommended_experiments) == (
        "PLAN-1",
        "PLAN-2",
    )


def test_report_builder_creates_summary_from_the_partially_populated_report():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    report = ReportBuilder().build(Project(), context)

    assert report.assessment_summary is not None
    assert report.assessment_summary.experiments == ()
    assert report.assessment_summary.findings == ()
    assert report.assessment_summary.applicable_actions == ()


def test_console_uses_exact_section_order_and_measurement_status(capsys):
    output = render(summarized_report(), capsys)
    sections = (
        "Measurement Status",
        "Main Findings",
        "Applicable Actions",
        "Blocked Actions",
        "Recommended Experiments",
        "Technical Notice",
    )

    assert [output.index(section) for section in sections] == sorted(
        output.index(section) for section in sections
    )
    assert "- baseline: READY" in output
    assert "- exp-001: INCOMPLETE" in output
    for family, status in AssessmentSummaryPresenter().present(
        source_report()
    ).readiness_statuses:
        assert f"- {family}: {status}" in output


def test_console_preserves_findings_actions_and_experiments(capsys):
    output = render(summarized_report(), capsys)

    first = output.index("OBSERVATION-1: First finding")
    second = output.index("OBSERVATION-2: Second finding")
    assert first < second
    assert "First description." in output
    assert "Second description." in output
    assert "ACTION-1: Title ACTION-1" in output
    assert "Applicability: APPLICABLE" in output
    assert "ACTION-3: Title ACTION-3" in output
    assert "Applicability: BLOCKED_BY_CONTRADICTION" in output
    assert "Justification: ACTION-RULE-1:REASONING-1:CONCLUSION-1" in output
    assert "ACTION-5" not in output
    assert "PLAN-1: Objective PLAN-1" in output
    assert "Status: READY" in output
    assert output.index("PLAN-1:") < output.index("PLAN-2:")


def test_console_handles_each_absent_section_independently(capsys):
    report = Report(project_name="empty")

    output = render(report, capsys)

    assert "No technical analysis readiness information is available." in output
    assert "No assessment findings are available." in output
    assert "No applicable actions are available." in output
    assert "No blocked actions are available." in output
    assert "No recommended experiments are available." in output


def test_console_omits_internal_scores_thresholds_and_traceability(capsys):
    output = render(summarized_report(), capsys)

    for forbidden in (
        "Global score",
        "Confidence",
        "Threshold",
        "Applied rules",
        "Traceability",
        "Supporting evidence",
    ):
        assert forbidden not in output


def test_console_prints_complete_technical_notice(capsys):
    output = render(summarized_report(), capsys)

    assert "This summary presents existing deterministic report content." in output
    assert (
        "It does not add scientific analysis or establish scientific validity."
        in output
    )
    assert (
        "For complete identifiers, evidence and technical detail, "
        "use --full-assessment."
        in output
    )
    assert (
        "For technical analysis readiness details, use --analysis-readiness."
        in output
    )


def test_console_is_byte_deterministic_and_does_not_mutate_report(capsys):
    report = summarized_report()
    before = deepcopy(report)

    first = render(report, capsys)
    second = render(report, capsys)

    assert first.encode("utf-8") == second.encode("utf-8")
    assert report == before
