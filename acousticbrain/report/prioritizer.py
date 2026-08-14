from acousticbrain.models import (
    DiagnosticPriorityAnalysis,
    PrioritizedDiagnostic,
)


class DiagnosticPriorityAnalyzer:
    """Prépare l'ordre de présentation sans modifier les diagnostics."""

    IMPACT_SCORES = {
        "HIGH": 100.0,
        "MEDIUM": 70.0,
        "LOW": 40.0,
        "OK": 10.0,
        "INFO": 0.0,
    }

    def analyze(self, diagnostics):
        ordered = sorted(
            diagnostics,
            key=self._priority_score,
            reverse=True,
        )
        prioritized = []
        previous_score = None
        rank = 0

        for index, diagnostic in enumerate(ordered, start=1):
            priority_score = self._priority_score(diagnostic)
            if priority_score != previous_score:
                rank = index
                previous_score = priority_score

            prioritized.append(
                PrioritizedDiagnostic(
                    diagnostic=diagnostic,
                    priority_score=priority_score,
                    rank=rank,
                    justification=(
                        f"Impact {diagnostic.severity}, confiance "
                        f"{diagnostic.confidence} %."
                    ),
                    is_secondary=diagnostic.severity in {"OK", "INFO"},
                )
            )

        return DiagnosticPriorityAnalysis(
            prioritized_diagnostics=prioritized,
            tie_groups=self._tie_groups(prioritized),
        )

    def _priority_score(self, diagnostic):
        impact_score = self.IMPACT_SCORES.get(diagnostic.severity, 0.0)
        confidence_multiplier = 0.5 + diagnostic.confidence / 200.0
        return impact_score * confidence_multiplier

    @staticmethod
    def _tie_groups(prioritized):
        groups = {}
        for item in prioritized:
            groups.setdefault(item.priority_score, []).append(item)

        return [group for group in groups.values() if len(group) > 1]
