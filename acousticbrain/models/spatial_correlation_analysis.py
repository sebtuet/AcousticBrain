from dataclasses import dataclass, field

from .spatial_correlation import SpatialCorrelation


@dataclass
class SpatialCorrelationAnalysis:
    correlations: list[SpatialCorrelation] = field(default_factory=list)
    source_analyses: tuple[str, ...] = ()
    confidence: float = 0.0
