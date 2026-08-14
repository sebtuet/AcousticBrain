from dataclasses import dataclass, field

from .bass_decay_band_analysis import BassDecayBandAnalysis
from .bass_decay_band_difference import BassDecayBandDifference
from .bass_decay_channel_analysis import BassDecayChannelAnalysis
from .impulse_channel import ImpulseChannel


@dataclass
class BassDecayAnalysis:
    """Agrégation multi-canal des faits de décroissance basse fréquence."""

    channel_analyses: dict[ImpulseChannel, BassDecayChannelAnalysis] = field(
        default_factory=dict
    )
    available_channels: tuple[ImpulseChannel, ...] = ()
    aggregate_bands: list[BassDecayBandAnalysis] = field(default_factory=list)
    common_center_frequencies_hz: tuple[float, ...] = ()
    left_right_band_differences: list[BassDecayBandDifference] = field(
        default_factory=list
    )
    coverage: float = 0.0
    confidence: float = 0.0

    def __post_init__(self):
        if not 0.0 <= self.coverage <= 100.0:
            raise ValueError("Coverage must be between 0 and 100.")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Confidence must be between 0 and 100.")
        if any(channel not in self.channel_analyses for channel in self.available_channels):
            raise ValueError("Available channels must have a channel analysis.")
