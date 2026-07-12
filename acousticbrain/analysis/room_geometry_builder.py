from math import isfinite

from acousticbrain.models import (
    GeometryOpening,
    GeometryPoint,
    GeometrySource,
    Room,
    RoomDescription,
    RoomDimensions,
    RoomGeometry,
    RoomGeometryModel,
    RoomOpeningSurface,
    RoomSurface,
    RoomSurfaceKind,
)
from acousticbrain.validation import RoomDescriptionValidator


class RoomGeometryBuildException(ValueError):
    """Refus de construction sans exposition d'une géométrie partielle."""

    def __init__(self, errors):
        self.errors = tuple(errors)
        super().__init__("Room description is geometrically invalid.")


class RoomGeometryBuilder:
    """Construit explicitement une géométrie depuis une seule source."""

    MODEL_VERSION = 1
    BASE_COMPLETENESS = 60.0
    SPEAKER_COMPLETENESS = 20.0
    LISTENING_COMPLETENESS = 20.0

    _OPENING_SURFACE_IDS = {
        RoomOpeningSurface.FRONT_WALL: "front_wall",
        RoomOpeningSurface.REAR_WALL: "rear_wall",
        RoomOpeningSurface.LEFT_WALL: "left_wall",
        RoomOpeningSurface.RIGHT_WALL: "right_wall",
    }

    def __init__(self, validator=None):
        self.validator = validator or RoomDescriptionValidator()

    def from_description(self, description: RoomDescription) -> RoomGeometry:
        if not isinstance(description, RoomDescription):
            raise TypeError(
                "RoomGeometryBuilder.from_description requires RoomDescription."
            )
        validation = self.validator.validate(description)
        if not validation.is_valid:
            raise RoomGeometryBuildException(validation.errors)

        dimensions = description.dimensions
        speakers = tuple(
            self._point(
                item.speaker_id,
                item.x_m,
                item.y_m,
                item.z_m,
            )
            for item in sorted(
                description.speakers,
                key=lambda item: item.speaker_id,
            )
        )
        listening_positions = tuple(
            self._point(
                item.position_id,
                item.x_m,
                item.y_m,
                item.z_m,
            )
            for item in sorted(
                description.listening_positions,
                key=lambda item: item.position_id,
            )
        )
        openings = tuple(
            GeometryOpening(
                opening_id=item.opening_id,
                surface_id=self._OPENING_SURFACE_IDS[item.surface],
                horizontal_offset_m=item.horizontal_offset_m,
                vertical_offset_m=item.vertical_offset_m,
                width_m=item.width_m,
                height_m=item.height_m,
            )
            for item in sorted(
                description.openings,
                key=lambda item: item.opening_id,
            )
        )
        completeness = self.BASE_COMPLETENESS
        if speakers:
            completeness += self.SPEAKER_COMPLETENESS
        if listening_positions:
            completeness += self.LISTENING_COMPLETENESS

        return self._geometry(
            dimensions=dimensions,
            speakers=speakers,
            listening_positions=listening_positions,
            openings=openings,
            source=GeometrySource.ROOM_DESCRIPTION,
            completeness=completeness,
        )

    def from_legacy_room(self, room: Room) -> RoomGeometry:
        if not isinstance(room, Room):
            raise TypeError(
                "RoomGeometryBuilder.from_legacy_room requires Room."
            )
        values = (room.length, room.width, room.height)
        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            and value > 0.0
            for value in values
        ):
            raise ValueError(
                "Legacy-room dimensions must be positive finite numbers."
            )
        dimensions = RoomDimensions(
            length_m=room.length,
            width_m=room.width,
            height_m=room.height,
        )
        return self._geometry(
            dimensions=dimensions,
            speakers=(),
            listening_positions=(),
            openings=(),
            source=GeometrySource.LEGACY_ROOM,
            completeness=self.BASE_COMPLETENESS,
        )

    @classmethod
    def _geometry(
        cls,
        *,
        dimensions,
        speakers,
        listening_positions,
        openings,
        source,
        completeness,
    ):
        return RoomGeometry(
            dimensions=dimensions,
            surfaces=cls._surfaces(dimensions),
            speakers=speakers,
            listening_positions=listening_positions,
            openings=openings,
            source=source,
            model=RoomGeometryModel.RECTANGULAR,
            model_version=cls.MODEL_VERSION,
            completeness=completeness,
        )

    @classmethod
    def _surfaces(cls, dimensions):
        length = dimensions.length_m
        width = dimensions.width_m
        height = dimensions.height_m
        specifications = (
            ("front_wall", RoomSurfaceKind.FRONT_WALL, 0.0, 0.0, 0.0, width, height),
            ("rear_wall", RoomSurfaceKind.REAR_WALL, length, 0.0, 0.0, width, height),
            ("left_wall", RoomSurfaceKind.LEFT_WALL, 0.0, 0.0, 0.0, length, height),
            ("right_wall", RoomSurfaceKind.RIGHT_WALL, 0.0, width, 0.0, length, height),
            ("floor", RoomSurfaceKind.FLOOR, 0.0, 0.0, 0.0, length, width),
            ("ceiling", RoomSurfaceKind.CEILING, 0.0, 0.0, height, length, width),
        )
        return tuple(
            RoomSurface(
                surface_id=surface_id,
                kind=kind,
                origin=cls._point(
                    f"{surface_id}.origin",
                    x_m,
                    y_m,
                    z_m,
                ),
                width_m=local_width,
                height_m=local_height,
            )
            for (
                surface_id,
                kind,
                x_m,
                y_m,
                z_m,
                local_width,
                local_height,
            ) in specifications
        )

    @staticmethod
    def _point(point_id, x_m, y_m, z_m):
        return GeometryPoint(
            point_id=point_id,
            x_m=x_m,
            y_m=y_m,
            z_m=z_m,
        )
