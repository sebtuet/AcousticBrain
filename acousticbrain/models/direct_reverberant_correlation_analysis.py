from dataclasses import dataclass, field

from .direct_reverberant_correlation import DirectReverberantCorrelation


@dataclass
class DirectReverberantCorrelationAnalysis:
    """Ensemble structuré des corrélations énergétiques D/R."""

    correlations: list[DirectReverberantCorrelation] = field(
        default_factory=list
    )
    source_analyses: tuple[str, ...] = ()
    confidence: float = 0.0
