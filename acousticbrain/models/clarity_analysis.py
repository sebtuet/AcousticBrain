from dataclasses import dataclass, field

from .clarity_band_analysis import ClarityBandAnalysis
from .clarity_channel_analysis import ClarityChannelAnalysis
from .impulse_channel import ImpulseChannel


@dataclass
class ClarityAnalysis:
    """Agrégation multi-canal des indicateurs de clarté et définition."""

    channel_analyses: dict[ImpulseChannel, ClarityChannelAnalysis] = field(
        default_factory=dict
    )
    available_channels: tuple[ImpulseChannel, ...] = ()
    aggregate_bands: list[ClarityBandAnalysis] = field(default_factory=list)
    common_center_frequencies_hz: tuple[float, ...] = ()
    left_right_c50_differences_db: dict[float, float] = field(
        default_factory=dict
    )
    left_right_c80_differences_db: dict[float, float] = field(
        default_factory=dict
    )
    left_right_d50_differences_percent: dict[float, float] = field(
        default_factory=dict
    )
    left_right_ts_differences_s: dict[float, float] = field(
        default_factory=dict
    )
    confidence: float = 0.0

