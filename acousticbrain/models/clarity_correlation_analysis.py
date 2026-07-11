from dataclasses import dataclass, field

from .clarity_correlation import ClarityCorrelation


@dataclass
class ClarityCorrelationAnalysis:
    """Ensemble structuré des corrélations de clarté disponibles."""

    correlations: list[ClarityCorrelation] = field(default_factory=list)
    source_analyses: tuple[str, ...] = ()
    confidence: float = 0.0
