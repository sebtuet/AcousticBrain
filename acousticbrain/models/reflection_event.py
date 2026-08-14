from dataclasses import dataclass


@dataclass(frozen=True)
class ReflectionEvent:
    """Événement temporel mesuré après le son direct."""

    delay_ms: float
    relative_level_db: float
    absolute_time_s: float
    sample_index: int
    acoustic_path_difference_m: float
    confidence: float

