from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace

from acousticbrain.report import (
    AcousticObservationConsoleReporter,
    DeterministicAcousticReasoningConsoleReporter,
    DeterministicCorrectiveActionConsoleReporter,
    DeterministicEvidenceWeightingConsoleReporter,
    EvidenceAcquisitionPlanConsoleReporter,
    FullAssessmentConsoleReporter,
    Report,
)


class RecordingReporter:
    def __init__(self, name, calls):
        self.name = name
        self.calls = calls

    def print(self, report):
        self.calls.append((self.name, report))


def render(reporter, report):
    output = StringIO()
    with redirect_stdout(output):
        reporter.print(report)
    return output.getvalue()


def test_default_reporters_have_the_required_historical_order():
    reporter = FullAssessmentConsoleReporter()

    assert tuple(type(item) for item in reporter.reporters) == (
        AcousticObservationConsoleReporter,
        DeterministicAcousticReasoningConsoleReporter,
        DeterministicCorrectiveActionConsoleReporter,
        DeterministicEvidenceWeightingConsoleReporter,
        EvidenceAcquisitionPlanConsoleReporter,
    )


def test_delegates_the_same_report_in_exact_order_without_mutation():
    calls = []
    reporters = tuple(
        RecordingReporter(name, calls)
        for name in ("observations", "reasoning", "actions", "weighting", "plans")
    )
    reporter = FullAssessmentConsoleReporter(reporters=reporters)
    report = Report(project_name="same-report")
    before = dict(report.__dict__)

    reporter.print(report)

    assert calls == [(name, report) for name in (
        "observations",
        "reasoning",
        "actions",
        "weighting",
        "plans",
    )]
    assert report.__dict__ == before


def test_empty_sections_are_printed_in_exact_order():
    output = render(
        FullAssessmentConsoleReporter(),
        Report(project_name="empty-assessment"),
    )
    headings = (
        "DETERMINISTIC ACOUSTIC OBSERVATIONS",
        "DETERMINISTIC ACOUSTIC REASONING",
        "DETERMINISTIC CORRECTIVE ACTIONS",
        "DETERMINISTIC EVIDENCE WEIGHTING",
        "NEXT RECOMMENDED EXPERIMENT",
    )

    assert all(heading in output for heading in headings)
    assert tuple(output.index(heading) for heading in headings) == tuple(
        sorted(output.index(heading) for heading in headings)
    )
    assert "No deterministic acoustic observation is available." in output
    assert "No deterministic acoustic reasoning is available." in output
    assert "No deterministic corrective action is available." in output
    assert "No existing evidence object is available for weighting." in output
    assert "No evidence acquisition plan was produced." in output
    assert "Plan coverage status" not in output


def test_present_and_empty_sections_are_printed_deterministically():
    report = Report(project_name="partial-assessment")
    report.acoustic_observations = SimpleNamespace(
        observations=(
            SimpleNamespace(
                observation_id="OBSERVATION_A",
                category="GENERAL",
                title="Observed fact",
                description="A deterministic observation.",
                confidence=None,
                supporting_evidence=("fact.a",),
                contradicting_evidence=(),
                limitations=("limited",),
                source_analysis_ids=("analysis.a",),
            ),
        )
    )

    first = render(FullAssessmentConsoleReporter(), report)
    second = render(FullAssessmentConsoleReporter(), report)

    assert first.encode() == second.encode()
    assert "OBSERVATION_A" in first
    assert "No deterministic acoustic observation is available." not in first
    assert "No deterministic acoustic reasoning is available." in first
    assert "No deterministic corrective action is available." in first
    assert "No existing evidence object is available for weighting." in first
    assert "No evidence acquisition plan was produced." in first


def test_two_empty_assessments_are_byte_for_byte_identical():
    report = Report(project_name="deterministic-assessment")

    first = render(FullAssessmentConsoleReporter(), report)
    second = render(FullAssessmentConsoleReporter(), report)

    assert first.encode() == second.encode()
