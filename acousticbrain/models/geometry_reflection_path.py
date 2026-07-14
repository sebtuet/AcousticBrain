from dataclasses import dataclass
from math import isfinite

from .geometry_coordinate import GeometryCoordinate
from .reflection_surface import ReflectionSurface
from .reflection_path_geometry import ReflectionPathGeometry


@dataclass(frozen=True)
class GeometryReflectionPath:
    path_id: str
    speaker_id: str
    listening_position_id: str
    surface_id: str
    base_surface_id: str
    surface: ReflectionSurface
    impact_point: GeometryCoordinate
    direct_path_m: float
    reflected_path_m: float
    acoustic_path_difference_m: float
    theoretical_delay_ms: float
    uncertainty_ms: float | None
    confidence: float | None
    provenance_codes: tuple[str, ...]
    path_geometry: ReflectionPathGeometry | None = None

    def __post_init__(self):
        identifiers = (
            self.path_id,
            self.speaker_id,
            self.listening_position_id,
            self.surface_id,
            self.base_surface_id,
        )
        if any(not isinstance(value, str) or not value for value in identifiers):
            raise ValueError("Geometry reflection-path identifiers are required.")
        if not isinstance(self.surface, ReflectionSurface):
            raise ValueError("Geometry reflection path requires a surface.")
        if not isinstance(self.impact_point, GeometryCoordinate):
            raise ValueError("Geometry reflection path requires an impact point.")
        values = (
            self.direct_path_m,
            self.reflected_path_m,
            self.acoustic_path_difference_m,
            self.theoretical_delay_ms,
        )
        if any(not isfinite(value) or value < 0.0 for value in values):
            raise ValueError("Geometry reflection-path values must be non-negative.")
        if self.uncertainty_ms is not None and (
            not isfinite(self.uncertainty_ms) or self.uncertainty_ms < 0.0
        ):
            raise ValueError("Geometry reflection uncertainty must be non-negative.")
        if self.confidence is not None and (
            not isfinite(self.confidence) or not 0.0 <= self.confidence <= 100.0
        ):
            raise ValueError("Geometry reflection confidence must be bounded.")
        if not isinstance(self.provenance_codes, tuple):
            raise ValueError("Geometry reflection provenance must be a tuple.")
        if self.path_geometry is not None and not isinstance(
            self.path_geometry, ReflectionPathGeometry
        ):
            raise ValueError("Geometry reflection path geometry has an invalid type.")
