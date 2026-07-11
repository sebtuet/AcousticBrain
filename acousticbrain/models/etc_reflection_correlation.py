from dataclasses import dataclass

from .impulse_channel import ImpulseChannel
from .reflection_event import ReflectionEvent
from .reflection_surface import ReflectionSurface


@dataclass(frozen=True)
class ETCReflectionCorrelation:
    """Correspondance structurée entre un événement ETC et un candidat SBIR."""

    code: str
    channel: ImpulseChannel
    event: ReflectionEvent
    surface: ReflectionSurface
    theoretical_delay_ms: float
    measured_delay_ms: float
    timing_error_ms: float
    acoustic_path_difference_m: float
    match_score: float
    confidence: float
    source_analyses: tuple[str, ...]

