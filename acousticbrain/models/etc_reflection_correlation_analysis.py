from dataclasses import dataclass, field

from .etc_reflection_correlation import ETCReflectionCorrelation
from .impulse_channel import ImpulseChannel
from .reflection_event import ReflectionEvent
from .reflection_surface import ReflectionSurface


@dataclass
class ETCReflectionCorrelationAnalysis:
    """Résultat explicite des rapprochements ETC-SBIR."""

    correlations: list[ETCReflectionCorrelation] = field(default_factory=list)
    unmatched_events: dict[ImpulseChannel, list[ReflectionEvent]] = field(
        default_factory=dict
    )
    available_surfaces: tuple[ReflectionSurface, ...] = ()
    evaluated_event_count: int = 0
    matched_event_count: int = 0
    confidence: float = 0.0

