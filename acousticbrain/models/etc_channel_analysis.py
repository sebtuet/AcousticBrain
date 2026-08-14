from dataclasses import dataclass, field

from .impulse_channel import ImpulseChannel
from .reflection_event import ReflectionEvent


@dataclass
class ETCChannelAnalysis:
    """Analyse factuelle des événements temporels d'un canal."""

    channel: ImpulseChannel
    direct_sound_time_s: float | None
    direct_sound_index: int | None
    events: list[ReflectionEvent] = field(default_factory=list)
    analysis_window_ms: float = 0.0
    noise_floor_db: float | None = None
    confidence: float = 0.0

