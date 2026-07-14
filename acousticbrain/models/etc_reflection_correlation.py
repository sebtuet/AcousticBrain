from dataclasses import dataclass
from math import isfinite

from .impulse_channel import ImpulseChannel
from .reflection_event import ReflectionEvent
from .reflection_surface import ReflectionSurface
from .geometry_coordinate import GeometryCoordinate


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
    surface_id: str | None = None
    impact_point: GeometryCoordinate | None = None
    geometric_uncertainty_ms: float | None = None
    geometry_confidence: float | None = None
    geometry_path_id: str | None = None
    provenance_codes: tuple[str, ...] = ()

    def __post_init__(self):
        geometry_values = (
            self.surface_id,
            self.impact_point,
            self.geometric_uncertainty_ms,
            self.geometry_confidence,
            self.geometry_path_id,
        )
        if any(value is not None for value in geometry_values) and any(
            value is None for value in geometry_values
        ):
            raise ValueError(
                "Geometry correlations require a complete testable surface match."
            )
        if self.surface_id is not None:
            if not self.surface_id.strip() or not self.geometry_path_id.strip():
                raise ValueError("Geometry correlation identifiers are required.")
            if (
                not isfinite(self.geometric_uncertainty_ms)
                or self.geometric_uncertainty_ms < 0.0
            ):
                raise ValueError("Geometry timing uncertainty must be non-negative.")
            if (
                not isfinite(self.geometry_confidence)
                or not 0.0 <= self.geometry_confidence <= 100.0
            ):
                raise ValueError("Geometry confidence must be bounded.")
            if not self.provenance_codes:
                raise ValueError("Geometry correlation provenance is required.")
