from acousticbrain.report.prioritizer import DiagnosticPriorityAnalyzer


class PrioritizationStage:
    """Prépare l'ordre de présentation après la production des diagnostics."""

    def run(self, report):
        report.diagnostic_priority = DiagnosticPriorityAnalyzer().analyze(
            report.diagnostics
        )
