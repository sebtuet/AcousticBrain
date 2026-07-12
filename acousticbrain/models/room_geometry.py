from dataclasses import dataclass
from math import isfinite

from .geometry_opening import GeometryOpening
from .geometry_point import GeometryPoint
from .geometry_source import GeometrySource
from .room_dimensions import RoomDimensions
from .room_geometry_model import RoomGeometryModel
from .room_surface import RoomSurface
from .geometry_speaker_orientation import GeometrySpeakerOrientation
from .geometry_surface_material import GeometrySurfaceMaterial
from .geometry_covering_zone import GeometryCoveringZone
from .geometry_furniture import GeometryFurniture
from .geometry_acoustic_treatment import GeometryAcousticTreatment
from .room_feature_geometry_completeness import RoomFeatureGeometryCompleteness


@dataclass(frozen=True)
class RoomGeometry:
    """Représentation géométrique validable, indépendante de l'UI."""

    dimensions: RoomDimensions
    surfaces: tuple[RoomSurface, ...]
    speakers: tuple[GeometryPoint, ...] = ()
    listening_positions: tuple[GeometryPoint, ...] = ()
    openings: tuple[GeometryOpening, ...] = ()
    source: GeometrySource = GeometrySource.LEGACY_ROOM
    model: RoomGeometryModel = RoomGeometryModel.RECTANGULAR
    model_version: int = 1
    completeness: float = 0.0
    speaker_orientations: tuple[GeometrySpeakerOrientation, ...] = ()
    surface_materials: tuple[GeometrySurfaceMaterial, ...] = ()
    covering_zones: tuple[GeometryCoveringZone, ...] = ()
    furniture: tuple[GeometryFurniture, ...] = ()
    acoustic_treatments: tuple[GeometryAcousticTreatment, ...] = ()
    feature_completeness: RoomFeatureGeometryCompleteness | None = None

    def __post_init__(self):
        if not isinstance(self.dimensions, RoomDimensions):
            raise ValueError("Room geometry requires RoomDimensions.")
        typed_collections = (
            ("surfaces", self.surfaces, RoomSurface),
            ("speakers", self.speakers, GeometryPoint),
            ("listening positions", self.listening_positions, GeometryPoint),
            ("openings", self.openings, GeometryOpening),
            ("speaker orientations", self.speaker_orientations, GeometrySpeakerOrientation),
            ("surface materials", self.surface_materials, GeometrySurfaceMaterial),
            ("covering zones", self.covering_zones, GeometryCoveringZone),
            ("furniture", self.furniture, GeometryFurniture),
            ("acoustic treatments", self.acoustic_treatments, GeometryAcousticTreatment),
        )
        for name, collection, expected_type in typed_collections:
            if not isinstance(collection, tuple):
                raise ValueError(f"Room-geometry {name} must be a tuple.")
            if any(not isinstance(item, expected_type) for item in collection):
                raise ValueError(f"Room-geometry {name} contain an invalid type.")
        if not isinstance(self.source, GeometrySource):
            raise ValueError("Room geometry requires a GeometrySource.")
        if not isinstance(self.model, RoomGeometryModel):
            raise ValueError("Room geometry requires a RoomGeometryModel.")
        if (
            isinstance(self.model_version, bool)
            or not isinstance(self.model_version, int)
            or self.model_version < 1
        ):
            raise ValueError("Room-geometry model version must be positive.")
        if (
            isinstance(self.completeness, bool)
            or not isinstance(self.completeness, (int, float))
            or not isfinite(self.completeness)
            or not 0.0 <= self.completeness <= 100.0
        ):
            raise ValueError("Room-geometry completeness must be between 0 and 100.")
        if self.feature_completeness is not None and not isinstance(
            self.feature_completeness, RoomFeatureGeometryCompleteness
        ):
            raise ValueError("Room feature completeness has an invalid type.")
        self._require_unique(
            (surface.surface_id for surface in self.surfaces), "surface"
        )
        self._require_unique(
            (speaker.point_id for speaker in self.speakers), "speaker"
        )
        self._require_unique(
            (position.point_id for position in self.listening_positions),
            "listening-position",
        )
        self._require_unique(
            (opening.opening_id for opening in self.openings), "opening"
        )
        self._require_unique(
            (item.speaker_id for item in self.speaker_orientations),
            "speaker-orientation",
        )
        self._require_unique(
            (item.surface_id for item in self.surface_materials),
            "surface-material",
        )
        self._require_unique(
            (item.zone_id for item in self.covering_zones), "covering-zone"
        )
        self._require_unique(
            (item.furniture_id for item in self.furniture), "furniture"
        )
        self._require_unique(
            (item.treatment_id for item in self.acoustic_treatments),
            "acoustic-treatment",
        )
        speaker_ids = {speaker.point_id for speaker in self.speakers}
        if any(
            item.speaker_id not in speaker_ids
            for item in self.speaker_orientations
        ):
            raise ValueError("Geometry orientation must reference a speaker.")
        surface_ids = {surface.surface_id for surface in self.surfaces}
        referenced_surface_ids = {
            *(item.surface_id for item in self.surface_materials),
            *(item.surface_id for item in self.covering_zones),
            *(
                item.surface_id
                for item in self.acoustic_treatments
                if item.surface_id is not None
            ),
        }
        if not referenced_surface_ids.issubset(surface_ids):
            raise ValueError("Geometry feature must reference a room surface.")

    @staticmethod
    def _require_unique(values, kind):
        identifiers = tuple(values)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                f"Room geometry contains a duplicate {kind} identifier."
            )
