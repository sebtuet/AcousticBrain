from dataclasses import dataclass


@dataclass(frozen=True)
class RT60BandDifference:
    """Écart RT60 gauche-droite avec sa provenance technique."""

    center_frequency_hz: float
    difference_seconds: float
    left_rt60_seconds: float
    right_rt60_seconds: float
    confidence: float
    left_estimate: str | None
    right_estimate: str | None

