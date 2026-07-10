from dataclasses import dataclass, field

from .peak_classification import PeakClassification


@dataclass
class PeakClassificationAnalysis:
    classifications: list[PeakClassification] = field(default_factory=list)
    score: float = 0.0
    confidence: float = 0.0
