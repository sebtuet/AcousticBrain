from math import dist, sqrt

from acousticbrain.geometry import (
    derive_planar_basis,
    point_in_convex_polygon,
    project_point,
)
from acousticbrain.models import (
    GeometryCoordinate,
    GeometryEarlyReflectionAnalysis,
    GeometryReflectionPath,
    PlanarRegionRole,
    PlanarSurfaceRole,
    PropagationGeometry,
    ReflectionPathGeometry,
    ReflectionSurface,
)


class GeometryEarlyReflectionEngine:
    """Calcule les trajets spéculaires de premier ordre, sans attribution ETC."""

    SPEED_OF_SOUND_M_S = 343.0
    RULE_CODES = (
        "GEOMETRY_REQUIRE_ROOM_DESCRIPTION",
        "GEOMETRY_IMAGE_SOURCE_FIRST_ORDER",
        "GEOMETRY_PLANAR_CONVEX_SURFACES",
        "GEOMETRY_EXCLUDE_OPENING_IMPACTS",
        "GEOMETRY_EXCLUDE_OBSTRUCTED_PATHS",
        "GEOMETRY_PREFER_NAMED_PLACED_REGION",
        "GEOMETRY_PROPAGATE_DECLARED_UNCERTAINTY",
    )
    _REFLECTION_SURFACE = {
        PlanarSurfaceRole.FRONT_WALL: ReflectionSurface.FRONT_WALL,
        PlanarSurfaceRole.REAR_WALL: ReflectionSurface.REAR_WALL,
        PlanarSurfaceRole.LEFT_WALL: ReflectionSurface.LEFT_WALL,
        PlanarSurfaceRole.RIGHT_WALL: ReflectionSurface.RIGHT_WALL,
        PlanarSurfaceRole.FLOOR: ReflectionSurface.FLOOR,
        PlanarSurfaceRole.CEILING: ReflectionSurface.CEILING,
    }

    def analyze(self, geometry):
        if geometry is not None and not isinstance(geometry, PropagationGeometry):
            from acousticbrain.analysis.propagation_geometry import (
                RectangularPropagationEngine,
            )
            geometry = RectangularPropagationEngine().analyze(geometry).geometry
        if geometry is None or not geometry.speakers or not geometry.listening_positions:
            return GeometryEarlyReflectionAnalysis(
                paths=(),
                source_analysis_codes=("PropagationGeometryAnalysis",),
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
            source_analysis_codes=("PropagationGeometryAnalysis",),
            applied_rule_codes=self.RULE_CODES,
        )

    def _path(self, geometry, speaker, listener, surface):
        source = (speaker.x_m, speaker.y_m, speaker.z_m)
        receiver = (listener.x_m, listener.y_m, listener.z_m)
        origin = (surface.origin.x_m, surface.origin.y_m, surface.origin.z_m)
        normal = surface.normal
        signed_distance = self._dot(self._subtract(source, origin), normal)
        mirrored = tuple(
            value - 2.0 * signed_distance * normal[index]
            for index, value in enumerate(source)
        )
        direction = self._subtract(receiver, mirrored)
        denominator = self._dot(direction, normal)
        if abs(denominator) <= 1e-12:
            return None
        ratio = -self._dot(self._subtract(mirrored, origin), normal) / denominator
        if not 0.0 <= ratio <= 1.0:
            return None
        impact = tuple(
            mirrored[index] + ratio * direction[index] for index in range(3)
        )
        point = GeometryCoordinate(*impact)
        if not self._inside_surface(surface, point):
            return None
        if self._inside_region(
            geometry, surface.surface_id, PlanarRegionRole.OPENING, point
        ):
            return None
        if self._obstructed(geometry, source, impact, receiver):
            return None
        region = self._named_region(geometry, surface.surface_id, point)
        surface_id = region.region_id if region is not None else surface.surface_id
        direct = dist(source, receiver)
        reflected = dist(mirrored, receiver)
        difference = max(0.0, reflected - direct)
        delay_ms = difference / self.SPEED_OF_SOUND_M_S * 1000.0
        quality_ids = [speaker.point_id, listener.point_id, surface.surface_id]
        if region is not None:
            quality_ids.append(region.region_id)
        uncertainty_ms, confidence, provenance = self._quality(
            geometry, quality_ids
        )
        boundary_vector = tuple(-signed_distance * value for value in normal)
        boundary_distance = abs(signed_distance)
        boundary_direction = (
            tuple(value / boundary_distance for value in boundary_vector)
            if boundary_distance > 1e-12 else (0.0, 0.0, 0.0)
        )
        return GeometryReflectionPath(
            path_id=(
                f"geometry_reflection.{speaker.point_id}."
                f"{listener.point_id}.{surface_id}"
            ),
            speaker_id=speaker.point_id,
            listening_position_id=listener.point_id,
            surface_id=surface_id,
            base_surface_id=surface.surface_id,
            surface=self._REFLECTION_SURFACE[surface.role],
            impact_point=point,
            direct_path_m=direct,
            reflected_path_m=reflected,
            acoustic_path_difference_m=difference,
            theoretical_delay_ms=delay_ms,
            uncertainty_ms=uncertainty_ms,
            confidence=confidence,
            provenance_codes=provenance,
            path_geometry=ReflectionPathGeometry(
                surface_normal=surface.normal,
                speaker_to_surface_direction=boundary_direction,
                speaker_surface_distance_m=boundary_distance,
                propagation_scene_id=geometry.scene_id,
            ),
        )

    @staticmethod
    def _dot(first, second):
        return sum(a * b for a, b in zip(first, second))

    @staticmethod
    def _subtract(first, second):
        return tuple(a - b for a, b in zip(first, second))

    @staticmethod
    def _inside_surface(surface, point):
        polygon = tuple(project_point(item, surface)[:2] for item in surface.vertices)
        projected = project_point(point, surface)
        return abs(projected[2]) <= 1e-7 and point_in_convex_polygon(
            projected[:2], polygon
        )

    @classmethod
    def _inside_region(cls, geometry, surface_id, role, point):
        return any(
            item.surface_id == surface_id
            and item.role is role
            and cls._region_contains(item, point)
            for item in geometry.regions
        )

    @staticmethod
    def _region_contains(region, point):
        basis = derive_planar_basis(region.vertices)
        polygon = tuple(project_point(item, basis)[:2] for item in region.vertices)
        projected = project_point(point, basis)
        return abs(projected[2]) <= 1e-7 and point_in_convex_polygon(
            projected[:2], polygon
        )

    @classmethod
    def _named_region(cls, geometry, surface_id, point):
        candidates = []
        for item in geometry.regions:
            if (
                item.surface_id != surface_id
                or item.role not in {PlanarRegionRole.COVERING, PlanarRegionRole.TREATMENT}
                or not cls._region_contains(item, point)
            ):
                continue
            candidates.append((derive_planar_basis(item.vertices).area_m2, item.region_id, item))
        return min(candidates, default=(None, None, None))[2]

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
        for origin, target, minimum, maximum in zip(start, end, lower, upper):
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
