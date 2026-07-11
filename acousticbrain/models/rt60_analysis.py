from dataclasses import dataclass, field

from .rt60_band_analysis import RT60BandAnalysis
from .rt60_channel_analysis import RT60ChannelAnalysis
from .impulse_channel import ImpulseChannel


@dataclass
class RT60Analysis:
    """Agrégation RT60 structurée de plusieurs canaux."""

    channel_analyses: list[RT60ChannelAnalysis] = field(default_factory=list)
    available_channels: tuple[ImpulseChannel, ...] = ()
    aggregate_bands: list[RT60BandAnalysis] = field(default_factory=list)
    common_center_frequencies_hz: tuple[float, ...] = ()
    left_right_band_differences_seconds: dict[float, float] = field(
        default_factory=dict
    )
    interchannel_homogeneity: float | None = None
    broadband_rt60_seconds: float | None = None
    minimum_rt60_seconds: float | None = None
    maximum_rt60_seconds: float | None = None
    confidence: float = 0.0
