from dataclasses import dataclass, field

from .etc_channel_analysis import ETCChannelAnalysis
from .impulse_channel import ImpulseChannel


@dataclass
class ETCAnalysis:
    """Agrégation multi-canal des événements temporels mesurés."""

    channels: dict[ImpulseChannel, ETCChannelAnalysis] = field(
        default_factory=dict
    )
    available_channels: list[ImpulseChannel] = field(default_factory=list)
    common_event_count: int = 0
    left_only_event_count: int = 0
    right_only_event_count: int = 0
    confidence: float = 0.0

