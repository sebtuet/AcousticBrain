from math import dist

from acousticbrain.models import (
    GeometryCoordinate,
    GeometryEarlyReflectionAnalysis,
    GeometryReflectionPath,
    GeometrySource,
    ReflectionSurface,
    RoomSurfaceKind,
)


class GeometryEarlyReflectionEngine:
    """Calcule les trajets spéculaires de premier ordre, sans attribution ETC."""

    SPEED_OF_SOUND_M_S = 343.0
    RULE_CODES = (
        "GEOMETRY_REQUIRE_ROOM_DESCRIPTION",
        "GEOMETRY_IMAGE_SOURCE_FIRST_ORDER",
        "GEOMETRY_EXCLUDE_OPENING_IMPACTS",
        "GEOMETRY_EXCLUDE_OBSTRUCTED_PATHS",
        "GEOMETRY_PREFER_NAMED_PLACED_REGION",
        "GEOMETRY_PROPAGATE_DECLARED_UNCERTAINTY",
    )
    SURFACES = {
        RoomSurfaceKind.FRONT_WALL: (ReflectionSurface.FRONT_WALL, 0, 0.0),
        RoomSurfaceKind.REAR_WALL: (ReflectionSurface.REAR_WALL, 0, "length_m"),
        RoomSurfaceKind.LEFT_WALL: (ReflectionSurface.LEFT_WALL, 1, 0.0),
        RoomSurfaceKind.RIGHT_WALL: (ReflectionSurface.RIGHT_WALL, 1, "width_m"),
        RoomSurfaceKind.FLOOR: (ReflectionSurface.FLOOR, 2, 0.0),
        RoomSurfaceKind.CEILING: (ReflectionSurface.CEILING, 2, "height_m"),
    }

    def analyze(self, geometry):
        if (
            geometry is None
            or geometry.source is not GeometrySource.ROOM_DESCRIPTION
            or not geometry.speakers
            or not geometry.listening_positions
        ):
            return GeometryEarlyReflectionAnalysis(
                paths=(),
                source_analysis_codes=("RoomGeometry",),
                applied_rule_codes=self.RULE_CODES,
            )
        paths = []
        for speaker in geometry.speakers:
            for listener in geometry.listening_positions:
                for surface in geometry.surfaces:
                    path = self._path(geometry, speaker, listener, surface)
                    if path is not None:
                        paths.append(path)
        return GeometryEarlyReflectionAnalysis(
            paths=tuple(sorted(paths, key=lambda item: item.path_id)),
            source_analysis_codes=("RoomGeometry",),
            applied_rule_codes=self.RULE_CODES,
        )

    def _path(self, geometry, speaker, listener, room_surface):
        reflection_surface, axis, plane_value = self.SURFACES[room_surface.kind]
        if isinstance(plane_value, str):
            plane_value = getattr(geometry.dimensions, plane_value)
        source = (speaker.x_m, speaker.y_m, speaker.z_m)
        receiver = (listener.x_m, listener.y_m, listener.z_m)
        mirrored = list(source)
        mirrored[axis] = 2.0 * plane_value - mirrored[axis]
        denominator = receiver[axis] - mirrored[axis]
        if denominator == 0.0:
            return None
        ratio = (plane_value - mirrored[axis]) / denominator
        if not 0.0 <= ratio <= 1.0:
            return None
        impact = tuple(
            mirrored[index] + ratio * (receiver[index] - mirrored[index])
            for index in range(3)
        )
        point = GeometryCoordinate(*impact)
        if self._inside_opening(geometry, room_surface.surface_id, reflection_surface, point):
            return None
        if self._obstructed(geometry, source, impact, receiver):
            return None
        surface_id = self._named_region_id(
            geometry, room_surface.surface_id, point
        ) or room_surface.surface_id
        direct = dist(source, receiver)
        reflected = dist(tuple(mirrored), receiver)
        difference = max(0.0, reflected - direct)
        delay_ms = difference / self.SPEED_OF_SOUND_M_S * 1000.0
        quality_ids = [speaker.point_id, listener.point_id, room_surface.surface_id]
        if surface_id != room_surface.surface_id:
            quality_ids.append(surface_id)
        uncertainty_ms, confidence, provenance = self._quality(
            geometry, quality_ids
        )
        return GeometryReflectionPath(
            path_id=(
                f"geometry_reflection.{speaker.point_id}."
                f"{listener.point_id}.{surface_id}"
            ),
            speaker_id=speaker.point_id,
            listening_position_id=listener.point_id,
            surface_id=surface_id,
            base_surface_id=room_surface.surface_id,
            surface=reflection_surface,
            impact_point=point,
            direct_path_m=direct,
            reflected_path_m=reflected,
            acoustic_path_difference_m=difference,
            theoretical_delay_ms=delay_ms,
            uncertainty_ms=uncertainty_ms,
            confidence=confidence,
            provenance_codes=provenance,
        )

    @staticmethod
    def _local_coordinates(surface, point):
        if surface in {ReflectionSurface.FRONT_WALL, ReflectionSurface.REAR_WALL}:
            return point.y_m, point.z_m
        if surface in {ReflectionSurface.LEFT_WALL, ReflectionSurface.RIGHT_WALL}:
            return point.x_m, point.z_m
        return point.x_m, point.y_m

    @classmethod
    def _inside_opening(cls, geometry, surface_id, surface, point):
        horizontal, vertical = cls._local_coordinates(surface, point)
        return any(
            item.surface_id == surface_id
            and item.horizontal_offset_m <= horizontal <= (
                item.horizontal_offset_m + item.width_m
            )
            and item.vertical_offset_m <= vertical <= (
                item.vertical_offset_m + item.height_m
            )
            for item in geometry.openings
        )

    @staticmethod
    def _contains(rectangle, point):
        if rectangle is None:
            return False
        minimum = rectangle.minimum_corner
        maximum = rectangle.maximum_corner
        return all(
            lower - 1e-9 <= value <= upper + 1e-9
            for value, lower, upper in zip(
                (point.x_m, point.y_m, point.z_m),
                (minimum.x_m, minimum.y_m, minimum.z_m),
                (maximum.x_m, maximum.y_m, maximum.z_m),
            )
        )

    @classmethod
    def _obstructed(cls, geometry, source, impact, receiver):
        boxes = tuple(
            item.bounding_box
            for item in geometry.furniture
            if item.bounding_box is not None
        )
        return any(
            cls._segment_intersects_box(start, end, box)
            for box in boxes
            for start, end in ((source, impact), (impact, receiver))
        )

    @staticmethod
    def _segment_intersects_box(start, end, box):
        lower = (
            box.minimum_corner.x_m,
            box.minimum_corner.y_m,
            box.minimum_corner.z_m,
        )
        upper = (
            box.maximum_corner.x_m,
            box.maximum_corner.y_m,
            box.maximum_corner.z_m,
        )
        minimum_t, maximum_t = 0.0, 1.0
        for origin, target, minimum, maximum in zip(
            start, end, lower, upper
        ):
            direction = target - origin
            if abs(direction) < 1e-12:
                if origin < minimum or origin > maximum:
                    return False
                continue
            first = (minimum - origin) / direction
            second = (maximum - origin) / direction
            if first > second:
                first, second = second, first
            minimum_t = max(minimum_t, first)
            maximum_t = min(maximum_t, second)
            if minimum_t > maximum_t:
                return False
        return True

    @classmethod
    def _named_region_id(cls, geometry, base_surface_id, point):
        candidates = [
            (item.placement.width_m * item.placement.height_m, item.treatment_id)
            for item in geometry.acoustic_treatments
            if item.surface_id == base_surface_id
            and cls._contains(item.placement, point)
        ]
        candidates.extend(
            (item.placement.width_m * item.placement.height_m, item.zone_id)
            for item in geometry.covering_zones
            if item.surface_id == base_surface_id
            and cls._contains(item.placement, point)
        )
        return min(candidates, default=(None, None))[1]

    @classmethod
    def _quality(cls, geometry, datum_ids):
        by_id = {item.datum_id: item for item in geometry.data_quality}
        values = [by_id.get(datum_id) for datum_id in datum_ids]
        if any(item is None for item in values):
            return None, None, ()
        path_uncertainty_m = 2.0 * sum(item.precision_m for item in values)
        uncertainty_ms = path_uncertainty_m / cls.SPEED_OF_SOUND_M_S * 1000.0
        confidence = min(item.confidence for item in values)
        provenance = tuple(dict.fromkeys(
            code for item in values for code in item.provenance_codes
        ))
        return uncertainty_ms, confidence, provenance
