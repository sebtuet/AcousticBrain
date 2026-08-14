from dataclasses import dataclass
from math import isfinite

from .acoustic_hypothesis import AcousticHypothesis


@dataclass(frozen=True)
class AcousticReasoningAnalysis:
    hypotheses: tuple[AcousticHypothesis, ...]
    source_analyses: tuple[str, ...]
    confidence: float

    def __post_init__(self):
        if not isinstance(self.hypotheses, tuple) or not isinstance(
            self.source_analyses, tuple
        ):
            raise ValueError("Reasoning-analysis collections must be tuples.")
        codes = tuple(item.code for item in self.hypotheses)
        if len(codes) != len(set(codes)):
            raise ValueError("Reasoning hypotheses must be unique.")
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Reasoning-analysis confidence must be bounded.")
