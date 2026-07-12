from dataclasses import dataclass

from .analysis_readiness import AnalysisReadiness


@dataclass(frozen=True)
class MeasurementReadinessAnalysis:
    """Ensemble des décisions de readiness, sans contrôle du pipeline."""

    analyses: tuple[AnalysisReadiness, ...] = ()
    confidence: float = 0.0
    source_analysis: str = "MeasurementQualityAnalysis"

    def __post_init__(self):
        if not isinstance(self.analyses, tuple):
            raise ValueError("Readiness analyses must be a tuple.")
        families = tuple(item.family for item in self.analyses)
        if len(families) != len(set(families)):
            raise ValueError("Readiness analysis families must be unique.")
        if not isinstance(self.confidence, (int, float)) or not (
            0.0 <= self.confidence <= 100.0
        ):
            raise ValueError("Readiness confidence must be between 0 and 100.")
        if not isinstance(self.source_analysis, str) or not self.source_analysis.strip():
            raise ValueError("Readiness source analysis is required.")
