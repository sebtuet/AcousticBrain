from dataclasses import dataclass
from math import isfinite

from .geometry_opening import GeometryOpening
from .geometry_point import GeometryPoint
from .geometry_source import GeometrySource
from .room_dimensions import RoomDimensions
from .room_geometry_model import RoomGeometryModel
from .room_surface import RoomSurface


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

    def __post_init__(self):
        if not isinstance(self.dimensions, RoomDimensions):
            raise ValueError("Room geometry requires RoomDimensions.")
        typed_collections = (
            ("surfaces", self.surfaces, RoomSurface),
            ("speakers", self.speakers, GeometryPoint),
            ("listening positions", self.listening_positions, GeometryPoint),
            ("openings", self.openings, GeometryOpening),
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

    @staticmethod
    def _require_unique(values, kind):
        identifiers = tuple(values)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                f"Room geometry contains a duplicate {kind} identifier."
            )
