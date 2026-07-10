from acousticbrain.brain.stages.prioritization import PrioritizationStage
from acousticbrain.diagnostics import Diagnostic
from acousticbrain.models import EvidenceLevel
from acousticbrain.report import Report


def test_prioritization_stage_stores_report_presentation_order():
    report = Report(project_name="Test")
    low = Diagnostic(
        title="Mineur",
        message="Diagnostic simulé.",
        severity="LOW",
        confidence=90,
        evidence_level=EvidenceLevel.OBSERVED,
    )
    high = Diagnostic(
        title="Prioritaire",
        message="Diagnostic simulé.",
        severity="HIGH",
        confidence=80,
        evidence_level=EvidenceLevel.OBSERVED,
    )
    report.add(low)
    report.add(high)

    PrioritizationStage().run(report)

    assert report.diagnostic_priority is not None
    assert [
        item.diagnostic for item in report.diagnostic_priority.prioritized_diagnostics
    ] == [high, low]
    assert report.diagnostics == [low, high]
