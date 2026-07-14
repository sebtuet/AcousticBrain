from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .geometry_coordinate import GeometryCoordinate
from .geometry_datum_quality import GeometryDatumQuality
from .geometry_furniture import GeometryFurniture
from .geometry_point import GeometryPoint
from .geometry_speaker_orientation import GeometrySpeakerOrientation
from .planar_geometry_description import PlanarRegionRole, PlanarSurfaceRole


class PropagationSceneSource(Enum):
    RECTANGULAR_ADAPTER = "RECTANGULAR_ADAPTER"
    DECLARED_PLANAR_SCENE = "DECLARED_PLANAR_SCENE"


@dataclass(frozen=True)
class PropagationSurface:
    surface_id: str
    role: PlanarSurfaceRole
    vertices: tuple[GeometryCoordinate, ...]
    origin: GeometryCoordinate
    u_axis: tuple[float, float, float]
    v_axis: tuple[float, float, float]
    normal: tuple[float, float, float]
    area_m2: float

    def __post_init__(self):
        if not isinstance(self.surface_id, str) or not self.surface_id.strip():
            raise ValueError("Propagation-surface identifier is required.")
        if not isinstance(self.role, PlanarSurfaceRole):
            raise ValueError("Propagation surface requires a role.")
        if len(self.vertices) < 3 or any(
            not isinstance(item, GeometryCoordinate) for item in self.vertices
        ):
            raise ValueError("Propagation surface requires typed vertices.")
        if not isinstance(self.origin, GeometryCoordinate):
            raise ValueError("Propagation surface requires an origin.")
        for vector in (self.u_axis, self.v_axis, self.normal):
            if not isinstance(vector, tuple) or len(vector) != 3 or any(
                not isfinite(value) for value in vector
            ):
                raise ValueError("Propagation-surface vectors must be finite triples.")
        if not isfinite(self.area_m2) or self.area_m2 <= 0.0:
            raise ValueError("Propagation-surface area must be positive.")


@dataclass(frozen=True)
class PropagationRegion:
    region_id: str
    surface_id: str
    role: PlanarRegionRole
    vertices: tuple[GeometryCoordinate, ...]
    feature_id: str | None = None

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.region_id, self.surface_id)
        ):
            raise ValueError("Propagation-region identifiers are required.")
        if not isinstance(self.role, PlanarRegionRole):
            raise ValueError("Propagation region requires a role.")
        if len(self.vertices) < 3 or any(
            not isinstance(item, GeometryCoordinate) for item in self.vertices
        ):
            raise ValueError("Propagation region requires typed vertices.")
        if self.feature_id is not None and (
            not isinstance(self.feature_id, str) or not self.feature_id.strip()
        ):
            raise ValueError("Propagation-region feature identifier is invalid.")


@dataclass(frozen=True)
class PropagationMaterialReference:
    assignment_id: str
    material_id: str
    surface_id: str | None = None
    region_id: str | None = None

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.assignment_id, self.material_id)
        ):
            raise ValueError("Propagation-material identifiers are required.")
        if sum(value is not None for value in (self.surface_id, self.region_id)) != 1:
            raise ValueError("Propagation material requires exactly one target reference.")


@dataclass(frozen=True)
class PropagationGeometry:
    scene_id: str
    scene_version: int
    scene_source: PropagationSceneSource
    surfaces: tuple[PropagationSurface, ...]
    regions: tuple[PropagationRegion, ...]
    speakers: tuple[GeometryPoint, ...]
    listening_positions: tuple[GeometryPoint, ...]
    speaker_orientations: tuple[GeometrySpeakerOrientation, ...] = ()
    furniture: tuple[GeometryFurniture, ...] = ()
    data_quality: tuple[GeometryDatumQuality, ...] = ()
    completeness: float = 0.0
    material_references: tuple[PropagationMaterialReference, ...] = ()

    def __post_init__(self):
        prefix, separator, digest = self.scene_id.partition(":")
        if prefix != "sha256" or not separator or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError("Propagation geometry requires a SHA-256 scene id.")
        if isinstance(self.scene_version, bool) or self.scene_version < 1:
            raise ValueError("Propagation scene version must be positive.")
        if not isinstance(self.scene_source, PropagationSceneSource):
            raise ValueError("Propagation geometry requires a scene source.")
        typed = (
            (self.surfaces, PropagationSurface),
            (self.regions, PropagationRegion),
            (self.speakers, GeometryPoint),
            (self.listening_positions, GeometryPoint),
            (self.speaker_orientations, GeometrySpeakerOrientation),
            (self.furniture, GeometryFurniture),
            (self.data_quality, GeometryDatumQuality),
            (self.material_references, PropagationMaterialReference),
        )
        for collection, expected in typed:
            if not isinstance(collection, tuple) or any(
                not isinstance(item, expected) for item in collection
            ):
                raise ValueError("Propagation geometry contains an invalid collection.")
        if not isfinite(self.completeness) or not 0.0 <= self.completeness <= 100.0:
            raise ValueError("Propagation completeness must be bounded.")
        self._unique((item.surface_id for item in self.surfaces), "surface")
        self._unique((item.region_id for item in self.regions), "region")
        self._unique(
            (item.assignment_id for item in self.material_references),
            "material-reference",
        )

    @staticmethod
    def _unique(values, kind):
        identifiers = tuple(values)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(f"Propagation geometry has duplicate {kind} identifiers.")


@dataclass(frozen=True)
class PropagationGeometryAnalysis:
    geometry: PropagationGeometry | None
    missing_fact_codes: tuple[str, ...]
    source_analysis_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]

    def __post_init__(self):
        if self.geometry is not None and not isinstance(
            self.geometry, PropagationGeometry
        ):
            raise ValueError("Propagation analysis geometry has an invalid type.")
        if any(
            not isinstance(values, tuple)
            for values in (
                self.missing_fact_codes,
                self.source_analysis_codes,
                self.applied_rule_codes,
            )
        ):
            raise ValueError("Propagation analysis trace fields must be tuples.")
