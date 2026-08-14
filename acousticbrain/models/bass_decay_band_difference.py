from dataclasses import dataclass


@dataclass(frozen=True)
class BassDecayBandDifference:
    """Écart gauche moins droite d'un temps de décroissance exploitable."""

    center_frequency_hz: float
    difference_seconds: float
    left_decay_time_seconds: float
    right_decay_time_seconds: float
    confidence: float
    left_method: str
    right_method: str

    def __post_init__(self):
        if self.left_decay_time_seconds <= 0.0 or self.right_decay_time_seconds <= 0.0:
            raise ValueError("Compared decay times must be positive.")
        expected = self.left_decay_time_seconds - self.right_decay_time_seconds
        if abs(self.difference_seconds - expected) > 1e-9:
            raise ValueError("Difference must equal left decay time minus right.")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Confidence must be between 0 and 100.")
