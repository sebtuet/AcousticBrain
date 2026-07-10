from contextlib import redirect_stdout
from io import StringIO

from acousticbrain.diagnostics import Diagnostic
from acousticbrain.models import (
    DiagnosticPriorityAnalysis,
    EvidenceLevel,
    PrioritizedDiagnostic,
)
from acousticbrain.report import ConsoleReporter, Report


def diagnostic(title):
    return Diagnostic(
        title=title,
        message="Diagnostic simulé.",
        severity="LOW",
        confidence=80,
        evidence_level=EvidenceLevel.OBSERVED,
    )


def render(report):
    output = StringIO()
    with redirect_stdout(output):
        ConsoleReporter().print(report)
    return output.getvalue()


def test_console_uses_the_existing_priority_order_and_marks_secondary_items():
    report = Report(project_name="Test")
    secondary = diagnostic("Secondaire")
    primary = diagnostic("Prioritaire")
    report.diagnostics = [secondary, primary]
    report.diagnostic_priority = DiagnosticPriorityAnalysis(
        prioritized_diagnostics=[
            PrioritizedDiagnostic(primary, 90, 1, "Priorité élevée.", False),
            PrioritizedDiagnostic(secondary, 30, 2, "Priorité basse.", True),
        ]
    )

    output = render(report)

    assert output.index("Prioritaire") < output.index("Secondaire")
    assert "Secondaire (secondaire)" in output
    assert report.diagnostics == [secondary, primary]


def test_console_preserves_diagnostic_order_without_prioritization():
    report = Report(project_name="Test")
    first = diagnostic("Premier")
    second = diagnostic("Deuxième")
    report.diagnostics = [first, second]

    output = render(report)

    assert output.index("Premier") < output.index("Deuxième")
