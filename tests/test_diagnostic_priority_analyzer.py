from acousticbrain.diagnostics import Diagnostic
from acousticbrain.models import EvidenceLevel
from acousticbrain.report.prioritizer import DiagnosticPriorityAnalyzer


def diagnostic(title, severity, confidence):
    return Diagnostic(
        title=title,
        message="Diagnostic simulé.",
        severity=severity,
        confidence=confidence,
        evidence_level=EvidenceLevel.OBSERVED,
    )


def test_prioritizes_diagnostics_by_impact_then_confidence():
    high = diagnostic("Prioritaire", "HIGH", 90)
    medium = diagnostic("Secondaire", "MEDIUM", 100)
    info = diagnostic("Information", "INFO", 100)

    analysis = DiagnosticPriorityAnalyzer().analyze([info, medium, high])

    prioritized = analysis.prioritized_diagnostics

    assert [item.diagnostic for item in prioritized] == [high, medium, info]
    assert [item.rank for item in prioritized] == [1, 2, 3]
    assert prioritized[0].priority_score > prioritized[1].priority_score
    assert prioritized[-1].is_secondary


def test_keeps_equally_prioritized_diagnostics_in_a_tie_group():
    first = diagnostic("Premier", "HIGH", 80)
    second = diagnostic("Deuxième", "HIGH", 80)

    analysis = DiagnosticPriorityAnalyzer().analyze([first, second])

    assert [item.rank for item in analysis.prioritized_diagnostics] == [1, 1]
    assert len(analysis.tie_groups) == 1
    assert [item.diagnostic for item in analysis.tie_groups[0]] == [first, second]
