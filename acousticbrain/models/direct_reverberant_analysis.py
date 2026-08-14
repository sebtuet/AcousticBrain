from dataclasses import dataclass, field

from .direct_reverberant_band_analysis import DirectReverberantBandAnalysis
from .direct_reverberant_channel_analysis import (
    DirectReverberantChannelAnalysis,
)
from .impulse_channel import ImpulseChannel


@dataclass
class DirectReverberantAnalysis:
    """Agrégation multi-canal des faits énergétiques D/R."""

    channel_analyses: dict[
        ImpulseChannel, DirectReverberantChannelAnalysis
    ] = field(default_factory=dict)
    available_channels: tuple[ImpulseChannel, ...] = ()
    aggregate_bands: list[DirectReverberantBandAnalysis] = field(
        default_factory=list
    )
    common_center_frequencies_hz: tuple[float, ...] = ()
    left_right_direct_to_reverberant_differences_db: dict[
        float, float
    ] = field(default_factory=dict)
    broadband_direct_to_reverberant_db: float | None = None
    minimum_broadband_direct_to_reverberant_db: float | None = None
    maximum_broadband_direct_to_reverberant_db: float | None = None
    confidence: float = 0.0
