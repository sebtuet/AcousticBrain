from copy import deepcopy

from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.models import (
    AnalysisReadiness,
    ImpulseChannel,
    Measurement,
    MeasurementAnalysisFamily,
    MeasurementQualityIssue,
    MeasurementQualityIssueCode,
    MeasurementQualityScope,
    MeasurementReadinessAnalysis,
    MeasurementReadinessStatus,
)
from acousticbrain.report import (
    AnalysisReadinessConsoleReporter,
    AnalysisReadinessPresenter,
    PresentedDiscoveredExperiment,
    PresentedExperimentDiscovery,
    Report,
)


class Project:
    name = "fixture"


def issue(code):
    return MeasurementQualityIssue(
        code=code,
        scope=MeasurementQualityScope.CHANNEL,
        channel=ImpulseChannel.LEFT,
        confidence=90.0,
        source_ids=("left-ir",),
    )


def readiness_analysis():
    reservation = issue(MeasurementQualityIssueCode.CLIPPING_DETECTED)
    blocker = issue(MeasurementQualityIssueCode.INVALID_DIRECT_PEAK)
    decisions = (
        AnalysisReadiness(
            family=MeasurementAnalysisFamily.FREQUENCY,
            status=MeasurementReadinessStatus.AVAILABLE,
        ),
        AnalysisReadiness(
            family=MeasurementAnalysisFamily.RT60,
            status=MeasurementReadinessStatus.AVAILABLE_WITH_RESERVATIONS,
            non_blocking_issues=(reservation,),
        ),
        AnalysisReadiness(
            family=MeasurementAnalysisFamily.ETC,
            status=MeasurementReadinessStatus.AVAILABLE,
        ),
        AnalysisReadiness(
            family=MeasurementAnalysisFamily.CLARITY,
            status=MeasurementReadinessStatus.BLOCKED,
            blocking_issues=(blocker,),
        ),
        AnalysisReadiness(
            family=MeasurementAnalysisFamily.SPATIAL,
            status=MeasurementReadinessStatus.AVAILABLE,
        ),
        AnalysisReadiness(
            family=MeasurementAnalysisFamily.DIRECT_REVERBERANT,
            status=MeasurementReadinessStatus.AVAILABLE,
        ),
        AnalysisReadiness(
            family=MeasurementAnalysisFamily.BASS_DECAY,
            status=MeasurementReadinessStatus.AVAILABLE,
        ),
    )
    return MeasurementReadinessAnalysis(analyses=decisions, confidence=90.0)


def experiments():
    return PresentedExperimentDiscovery(
        experiments=(
            PresentedDiscoveredExperiment(
                experiment_id="baseline",
                experiment_type="BASELINE",
                state="READY",
                file_count=3,
                timestamp="2026-07-27T00:00:00",
                available_channels=("LEFT", "RIGHT", "STEREO"),
            ),
            PresentedDiscoveredExperiment(
                experiment_id="exp-001",
                experiment_type="EXPERIMENT",
                state="INCOMPLETE",
                file_count=1,
                timestamp="2026-07-27T00:01:00",
                available_channels=("LEFT",),
            ),
        )
    )


def report_with_readiness():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.measurement_readiness_analysis = readiness_analysis()
    report = Report(project_name="fixture")
    report.experiments_discovered = experiments()
    report.analysis_readiness = AnalysisReadinessPresenter().present(context)
    return report


def render(report, capsys):
    AnalysisReadinessConsoleReporter().print(report)
    return capsys.readouterr().out


def test_presenter_projects_structured_readiness_directly_in_existing_order():
    source = readiness_analysis()
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.measurement_readiness_analysis = source

    presented = AnalysisReadinessPresenter().present(context)

    assert tuple(item.family for item in presented.analyses) == tuple(
        family.value for family in MeasurementAnalysisFamily
    )
    assert tuple(item.status for item in presented.analyses) == (
        "AVAILABLE",
        "AVAILABLE_WITH_RESERVATIONS",
        "AVAILABLE",
        "BLOCKED",
        "AVAILABLE",
        "AVAILABLE",
        "AVAILABLE",
    )
    assert presented.analyses[1].reservation_issue_codes == (
        "CLIPPING_DETECTED",
    )
    assert presented.analyses[3].blocking_issue_codes == (
        "INVALID_DIRECT_PEAK",
    )


def test_report_builder_projects_readiness_without_changing_pipeline_context():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.measurement_readiness_analysis = readiness_analysis()

    report = ReportBuilder().build(Project(), context)

    assert report.analysis_readiness == AnalysisReadinessPresenter().present(
        context
    )
    assert context.measurement_readiness_analysis is not None


def test_console_prints_only_contracted_information(capsys):
    output = render(report_with_readiness(), capsys)

    assert "- baseline: READY" in output
    assert "- exp-001: INCOMPLETE" in output
    positions = [output.index(f"\n{family.value}\n") for family in MeasurementAnalysisFamily]
    assert positions == sorted(positions)
    assert "Status: AVAILABLE_WITH_RESERVATIONS" in output
    assert "Status: BLOCKED" in output
    assert "Blocking issues\n- INVALID_DIRECT_PEAK" in output
    assert "Reservations\n- CLIPPING_DETECTED" in output
    for forbidden in (
        "Confidence",
        "Metric",
        "Threshold",
        "Applied rule",
        "Evidence",
        "Global score",
    ):
        assert forbidden not in output


def test_console_omits_empty_issue_sections(capsys):
    output = render(report_with_readiness(), capsys)
    frequency = output.split("\nFREQUENCY\n", 1)[1].split("\nRT60\n", 1)[0]
    rt60 = output.split("\nRT60\n", 1)[1].split("\nETC\n", 1)[0]
    clarity = output.split("\nCLARITY\n", 1)[1].split("\nSPATIAL\n", 1)[0]

    assert "Blocking issues" not in frequency
    assert "Reservations" not in frequency
    assert "Blocking issues" not in rt60
    assert "Reservations" in rt60
    assert "Blocking issues" in clarity
    assert "Reservations" not in clarity


def test_console_reports_absent_readiness_without_inventing_families(capsys):
    report = Report(project_name="fixture")
    report.experiments_discovered = experiments()

    output = render(report, capsys)

    assert "- baseline: READY" in output
    assert "- exp-001: INCOMPLETE" in output
    assert "No technical analysis readiness information is available." in output
    assert "Analysis Families" not in output
    assert "FREQUENCY" not in output
    assert "Status: BLOCKED" not in output


def test_console_explains_technical_scope_and_blocked_semantics(capsys):
    output = render(report_with_readiness(), capsys)

    assert "These statuses describe technical analysis readiness." in output
    assert "They do not establish scientific validity." in output
    assert (
        "BLOCKED does not mean that the current pipeline skipped computation."
        in output
    )


def test_console_is_deterministic_and_does_not_mutate_report(capsys):
    report = report_with_readiness()
    before = deepcopy(report)

    first = render(report, capsys)
    second = render(report, capsys)

    assert first == second
    assert report == before
