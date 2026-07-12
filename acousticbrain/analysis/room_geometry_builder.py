from math import isfinite

from acousticbrain.models import (
    GeometryAcousticTreatment,
    GeometryAcousticTreatmentType,
    GeometryBox,
    GeometryCoordinate,
    GeometryCoveringZone,
    GeometryFurniture,
    GeometryFurnitureType,
    GeometryMaterialType,
    GeometryOpening,
    GeometryPoint,
    GeometrySource,
    GeometrySpeakerOrientation,
    GeometrySurfaceMaterial,
    GeometrySurfaceRectangle,
    Room,
    RoomDescription,
    RoomDimensions,
    RoomGeometry,
    RoomGeometryModel,
    RoomOpeningSurface,
    RoomDescriptionSurface,
    RoomFeatureGeometryCompleteness,
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
    _DESCRIPTION_SURFACE_IDS = {
        RoomDescriptionSurface.FRONT_WALL: "front_wall",
        RoomDescriptionSurface.REAR_WALL: "rear_wall",
        RoomDescriptionSurface.LEFT_WALL: "left_wall",
        RoomDescriptionSurface.RIGHT_WALL: "right_wall",
        RoomDescriptionSurface.FLOOR: "floor",
        RoomDescriptionSurface.CEILING: "ceiling",
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
        speaker_orientations = tuple(
            GeometrySpeakerOrientation(
                speaker_id=item.speaker_id,
                yaw_degrees=(
                    item.orientation.yaw_degrees
                    if item.orientation is not None
                    else None
                ),
            )
            for item in sorted(
                description.speakers,
                key=lambda item: item.speaker_id,
            )
        )
        surface_materials = tuple(
            GeometrySurfaceMaterial(
                surface_id=self._DESCRIPTION_SURFACE_IDS[item.surface],
                material_type=GeometryMaterialType(item.material_type.value),
                detail=item.detail,
            )
            for item in sorted(
                description.surface_materials,
                key=lambda item: item.surface.value,
            )
        )
        covering_zones = tuple(
            GeometryCoveringZone(
                zone_id=item.zone_id,
                surface_id=self._DESCRIPTION_SURFACE_IDS[item.surface],
                material_type=GeometryMaterialType(item.material_type.value),
                detail=item.detail,
                placement=self._surface_rectangle(item, dimensions),
            )
            for item in sorted(
                description.covering_zones,
                key=lambda item: item.zone_id,
            )
        )
        furniture = tuple(
            GeometryFurniture(
                furniture_id=item.furniture_id,
                furniture_type=GeometryFurnitureType(item.furniture_type.value),
                detail=item.detail,
                bounding_box=self._furniture_box(item),
            )
            for item in sorted(
                description.furniture,
                key=lambda item: item.furniture_id,
            )
        )
        acoustic_treatments = tuple(
            GeometryAcousticTreatment(
                treatment_id=item.treatment_id,
                treatment_type=GeometryAcousticTreatmentType(
                    item.treatment_type.value
                ),
                detail=item.detail,
                surface_id=(
                    self._DESCRIPTION_SURFACE_IDS[item.surface]
                    if item.surface is not None
                    else None
                ),
                placement=self._surface_rectangle(item, dimensions),
            )
            for item in sorted(
                description.acoustic_treatments,
                key=lambda item: item.treatment_id,
            )
        )

        return self._geometry(
            dimensions=dimensions,
            speakers=speakers,
            listening_positions=listening_positions,
            openings=openings,
            source=GeometrySource.ROOM_DESCRIPTION,
            completeness=completeness,
            speaker_orientations=speaker_orientations,
            surface_materials=surface_materials,
            covering_zones=covering_zones,
            furniture=furniture,
            acoustic_treatments=acoustic_treatments,
            feature_completeness=self._feature_completeness(
                description,
                speaker_orientations,
                covering_zones,
                furniture,
                acoustic_treatments,
            ),
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
        speaker_orientations=(),
        surface_materials=(),
        covering_zones=(),
        furniture=(),
        acoustic_treatments=(),
        feature_completeness=None,
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
            speaker_orientations=speaker_orientations,
            surface_materials=surface_materials,
            covering_zones=covering_zones,
            furniture=furniture,
            acoustic_treatments=acoustic_treatments,
            feature_completeness=feature_completeness,
        )

    @classmethod
    def _surface_rectangle(cls, item, dimensions):
        if item.horizontal_offset_m is None:
            return None
        horizontal = item.horizontal_offset_m
        vertical = item.vertical_offset_m
        width = item.width_m
        height = item.height_m
        surface = item.surface
        if surface is RoomDescriptionSurface.FRONT_WALL:
            minimum = (0.0, horizontal, vertical)
            maximum = (0.0, horizontal + width, vertical + height)
        elif surface is RoomDescriptionSurface.REAR_WALL:
            minimum = (dimensions.length_m, horizontal, vertical)
            maximum = (
                dimensions.length_m,
                horizontal + width,
                vertical + height,
            )
        elif surface is RoomDescriptionSurface.LEFT_WALL:
            minimum = (horizontal, 0.0, vertical)
            maximum = (horizontal + width, 0.0, vertical + height)
        elif surface is RoomDescriptionSurface.RIGHT_WALL:
            minimum = (horizontal, dimensions.width_m, vertical)
            maximum = (
                horizontal + width,
                dimensions.width_m,
                vertical + height,
            )
        elif surface is RoomDescriptionSurface.FLOOR:
            minimum = (horizontal, vertical, 0.0)
            maximum = (horizontal + width, vertical + height, 0.0)
        else:
            minimum = (horizontal, vertical, dimensions.height_m)
            maximum = (
                horizontal + width,
                vertical + height,
                dimensions.height_m,
            )
        return GeometrySurfaceRectangle(
            horizontal_offset_m=horizontal,
            vertical_offset_m=vertical,
            width_m=width,
            height_m=height,
            minimum_corner=GeometryCoordinate(*minimum),
            maximum_corner=GeometryCoordinate(*maximum),
        )

    @staticmethod
    def _furniture_box(item):
        if item.x_m is None:
            return None
        return GeometryBox(
            minimum_corner=GeometryCoordinate(item.x_m, item.y_m, item.z_m),
            maximum_corner=GeometryCoordinate(
                item.x_m + item.length_m,
                item.y_m + item.width_m,
                item.z_m + item.height_m,
            ),
        )

    @staticmethod
    def _feature_completeness(
        description,
        orientations,
        zones,
        furniture,
        treatments,
    ):
        has_features = any(
            item.yaw_degrees is not None for item in orientations
        ) or any(
            (
                description.surface_materials,
                description.covering_zones,
                description.furniture,
                description.acoustic_treatments,
            )
        )
        if not has_features:
            return None

        def coverage(items, available):
            return 100.0 * available / len(items) if items else 0.0

        orientation_coverage = coverage(
            orientations,
            sum(item.yaw_degrees is not None for item in orientations),
        )
        material_coverage = 100.0 * len(description.surface_materials) / 6.0
        covering_coverage = coverage(
            zones, sum(item.placement is not None for item in zones)
        )
        furniture_coverage = coverage(
            furniture, sum(item.bounding_box is not None for item in furniture)
        )
        treatment_coverage = coverage(
            treatments, sum(item.placement is not None for item in treatments)
        )
        components = (
            orientation_coverage,
            material_coverage,
            covering_coverage,
            furniture_coverage,
            treatment_coverage,
        )
        return RoomFeatureGeometryCompleteness(
            orientation_coverage=orientation_coverage,
            material_coverage=material_coverage,
            covering_placement_coverage=covering_coverage,
            furniture_placement_coverage=furniture_coverage,
            treatment_placement_coverage=treatment_coverage,
            score=sum(components) / len(components),
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
