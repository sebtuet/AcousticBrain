from dataclasses import dataclass, field

from .impulse_channel import ImpulseChannel


@dataclass
class ImpulseResponse:
    """Échantillons bruts d'une réponse impulsionnelle pour un canal."""

    channel: ImpulseChannel
    sample_rate_hz: float
    samples: list[float] = field(default_factory=list)
    time_offset_seconds: float = 0.0
    source_id: str | None = None
    peak_value: float | None = None
    peak_index: int | None = None
    response_length: int | None = None
    sample_interval_s: float | None = None
    start_time_s: float | None = None
