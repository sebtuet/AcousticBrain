from dataclasses import dataclass, field

from .bass_decay_band_analysis import BassDecayBandAnalysis
from .decay_usability import DecayUsability
from .impulse_channel import ImpulseChannel


@dataclass
class BassDecayChannelAnalysis:
    """Agrégation factuelle des décroissances d'un canal."""

    channel: ImpulseChannel
    band_analyses: list[BassDecayBandAnalysis] = field(default_factory=list)
    covered_frequency_range_hz: tuple[float, float] | None = None
    maximum_observed_duration_seconds: float | None = None
    usable_band_count: int = 0
    confidence: float = 0.0
    method: str = ""

    def __post_init__(self):
        if self.covered_frequency_range_hz is not None:
            minimum, maximum = self.covered_frequency_range_hz
            if minimum >= maximum:
                raise ValueError("Covered frequency bounds must be ordered.")
        if (
            self.maximum_observed_duration_seconds is not None
            and self.maximum_observed_duration_seconds < 0.0
        ):
            raise ValueError("Maximum observed duration cannot be negative.")
        expected_count = sum(
            band.usability is DecayUsability.USABLE
            for band in self.band_analyses
        )
        if self.usable_band_count != expected_count:
            raise ValueError("Usable band count must match the band facts.")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Confidence must be between 0 and 100.")
