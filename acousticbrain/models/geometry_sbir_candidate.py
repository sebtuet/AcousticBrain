from dataclasses import dataclass
from math import isfinite

from .geometry_coordinate import GeometryCoordinate
from .reflection_surface import ReflectionSurface


@dataclass(frozen=True)
class GeometrySBIRCandidate:
    candidate_id: str
    geometry_path_id: str
    speaker_id: str
    listening_position_id: str
    surface_id: str
    base_surface_id: str
    surface: ReflectionSurface
    relationship_code: str
    impact_point: GeometryCoordinate
    direct_path_m: float
    reflected_path_m: float
    extra_distance_m: float
    speaker_boundary_distance_m: float
    expected_cancellation_frequency_hz: float
    distance_uncertainty_m: float | None
    frequency_uncertainty_hz: float | None
    confidence: float | None
    provenance_codes: tuple[str, ...]

    def __post_init__(self):
        identifiers = (
            self.candidate_id,
            self.geometry_path_id,
            self.speaker_id,
            self.listening_position_id,
            self.surface_id,
            self.base_surface_id,
            self.relationship_code,
        )
        if any(not isinstance(value, str) or not value.strip() for value in identifiers):
            raise ValueError("Geometry SBIR identifiers are required.")
        if not isinstance(self.surface, ReflectionSurface):
            raise ValueError("Geometry SBIR candidate requires a surface.")
        if not isinstance(self.impact_point, GeometryCoordinate):
            raise ValueError("Geometry SBIR candidate requires an impact point.")
        if not isfinite(self.direct_path_m) or self.direct_path_m < 0.0:
            raise ValueError("Geometry SBIR direct path must be non-negative.")
        values = (
            self.reflected_path_m,
            self.extra_distance_m,
            self.speaker_boundary_distance_m,
            self.expected_cancellation_frequency_hz,
        )
        if any(not isfinite(value) or value <= 0.0 for value in values):
            raise ValueError("Geometry SBIR physical values must be positive.")
        for value in (self.distance_uncertainty_m, self.frequency_uncertainty_hz):
            if value is not None and (not isfinite(value) or value < 0.0):
                raise ValueError("Geometry SBIR uncertainty must be non-negative.")
        if self.confidence is not None and (
            not isfinite(self.confidence) or not 0.0 <= self.confidence <= 100.0
        ):
            raise ValueError("Geometry SBIR confidence must be bounded.")
        if not isinstance(self.provenance_codes, tuple):
            raise ValueError("Geometry SBIR provenance must be a tuple.")


@dataclass(frozen=True)
class GeometrySBIRAnalysis:
    candidates: tuple[GeometrySBIRCandidate, ...]
    source_analysis_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.candidates, tuple) or any(
            not isinstance(item, GeometrySBIRCandidate) for item in self.candidates
        ):
            raise ValueError("Geometry SBIR candidates must be a typed tuple.")
        if any(
            not isinstance(values, tuple)
            for values in (self.source_analysis_codes, self.applied_rule_codes)
        ):
            raise ValueError("Geometry SBIR trace collections must be tuples.")
