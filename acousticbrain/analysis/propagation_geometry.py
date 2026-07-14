from abc import ABC, abstractmethod
from hashlib import sha256
import json

from acousticbrain.geometry import derive_planar_basis
from acousticbrain.models import (
    GeometryCoordinate,
    GeometrySource,
    PlanarRegionRole,
    PlanarSurfaceRole,
    PropagationGeometry,
    PropagationGeometryAnalysis,
    PropagationMaterialReference,
    PropagationRegion,
    PropagationSceneSource,
    PropagationSurface,
)
from acousticbrain.validation import RoomDescriptionValidator


class PropagationGeometryBuildException(ValueError):
    def __init__(self, errors):
        self.errors = tuple(errors)
        super().__init__("Declared planar propagation geometry is invalid.")


class PropagationGeometryEngine(ABC):
    SCENE_VERSION = 1

    @abstractmethod
    def analyze(self, room_geometry, room_description=None):
        raise NotImplementedError

    @classmethod
    def _surface(cls, surface_id, role, vertices):
        raw_coordinates = tuple(
            item if isinstance(item, GeometryCoordinate) else GeometryCoordinate(
                item.x_m, item.y_m, item.z_m
            )
            for item in vertices
        )
        coordinates = cls._canonical_coordinates(raw_coordinates)
        basis = derive_planar_basis(coordinates)
        return PropagationSurface(
            surface_id=surface_id,
            role=role,
            vertices=coordinates,
            origin=GeometryCoordinate(*basis.origin),
            u_axis=basis.u_axis,
            v_axis=basis.v_axis,
            normal=basis.normal,
            area_m2=basis.area_m2,
        )

    @classmethod
    def _analysis(cls, source, surfaces, regions, room_geometry, room_description=None):
        surfaces = tuple(sorted(surfaces, key=lambda item: item.surface_id))
        regions = tuple(sorted(regions, key=lambda item: item.region_id))
        scene_id = cls._scene_id(
            source,
            surfaces,
            regions,
            room_geometry.speakers,
            room_geometry.listening_positions,
            room_geometry.speaker_orientations,
            room_geometry.furniture,
            room_geometry.data_quality,
        )
        expected_roles = set(PlanarSurfaceRole)
        available_roles = {item.role for item in surfaces}
        geometry = PropagationGeometry(
            scene_id=scene_id,
            scene_version=cls.SCENE_VERSION,
            scene_source=source,
            surfaces=surfaces,
            regions=regions,
            speakers=room_geometry.speakers,
            listening_positions=room_geometry.listening_positions,
            speaker_orientations=room_geometry.speaker_orientations,
            furniture=room_geometry.furniture,
            data_quality=room_geometry.data_quality,
            completeness=100.0 * len(available_roles) / len(expected_roles),
            material_references=tuple(
                PropagationMaterialReference(
                    assignment_id=item.assignment_id,
                    material_id=item.material_id,
                    surface_id=item.surface_id,
                    region_id=item.region_id,
                )
                for item in sorted(
                    (
                        room_description.material_assignments
                        if room_description is not None else ()
                    ),
                    key=lambda item: item.assignment_id,
                )
            ),
        )
        return PropagationGeometryAnalysis(
            geometry=geometry,
            missing_fact_codes=tuple(
                f"PROPAGATION_SURFACE_ROLE_MISSING.{role.value}"
                for role in sorted(expected_roles - available_roles, key=lambda item: item.value)
            ),
            source_analysis_codes=("RoomGeometry", "RoomDescription"),
            applied_rule_codes=(
                "PROPAGATION_SCENE_EXCLUSIVE_SOURCE",
                "PROPAGATION_SCENE_CANONICAL_SHA256_ID",
                "PROPAGATION_SCENE_PRESERVE_GEOMETRY_QUALITY",
            ),
        )

    @staticmethod
    def _canonical_polygon(vertices):
        values = tuple((item.x_m, item.y_m, item.z_m) for item in vertices)
        variants = []
        for candidate in (values, tuple(reversed(values))):
            variants.extend(candidate[index:] + candidate[:index] for index in range(len(candidate)))
        return min(variants)

    @classmethod
    def _canonical_coordinates(cls, vertices):
        return tuple(
            GeometryCoordinate(*value) for value in cls._canonical_polygon(vertices)
        )

    @classmethod
    def _scene_id(
        cls, source, surfaces, regions, speakers, listeners, orientations,
        furniture, data_quality,
    ):
        payload = {
            "scene_version": cls.SCENE_VERSION,
            "scene_source": source.value,
            "surfaces": [
                (item.surface_id, item.role.value, cls._canonical_polygon(item.vertices))
                for item in surfaces
            ],
            "regions": [
                (
                    item.region_id,
                    item.surface_id,
                    item.role.value,
                    item.feature_id,
                    cls._canonical_polygon(item.vertices),
                )
                for item in regions
            ],
            "speakers": sorted((item.point_id, item.x_m, item.y_m, item.z_m) for item in speakers),
            "listeners": sorted((item.point_id, item.x_m, item.y_m, item.z_m) for item in listeners),
            "orientations": sorted((item.speaker_id, item.yaw_degrees) for item in orientations),
            "furniture": sorted(
                (
                    item.furniture_id,
                    None if item.bounding_box is None else (
                        item.bounding_box.minimum_corner.x_m,
                        item.bounding_box.minimum_corner.y_m,
                        item.bounding_box.minimum_corner.z_m,
                        item.bounding_box.maximum_corner.x_m,
                        item.bounding_box.maximum_corner.y_m,
                        item.bounding_box.maximum_corner.z_m,
                    ),
                )
                for item in furniture
            ),
            "quality": sorted(
                (item.datum_id, item.precision_m, item.confidence, item.provenance_codes)
                for item in data_quality
            ),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return f"sha256:{sha256(canonical.encode('utf-8')).hexdigest()}"


class PlanarPropagationEngine(PropagationGeometryEngine):
    def __init__(self, validator=None):
        self.validator = validator or RoomDescriptionValidator()

    def analyze(self, room_geometry, room_description=None):
        if room_description is None or not room_description.planar_surfaces:
            return PropagationGeometryAnalysis(
                geometry=None,
                missing_fact_codes=("PLANAR_SURFACES_MISSING",),
                source_analysis_codes=("RoomDescription",),
                applied_rule_codes=("PROPAGATION_REQUIRE_DECLARED_PLANAR_SURFACES",),
            )
        validation = self.validator.validate(room_description)
        if not validation.is_valid:
            raise PropagationGeometryBuildException(validation.errors)
        surfaces = tuple(
            self._surface(item.surface_id, item.role, item.vertices)
            for item in room_description.planar_surfaces
        )
        regions = tuple(
            PropagationRegion(
                region_id=item.region_id,
                surface_id=item.surface_id,
                role=item.role,
                vertices=tuple(
                    self._canonical_coordinates(tuple(
                        GeometryCoordinate(vertex.x_m, vertex.y_m, vertex.z_m)
                        for vertex in item.vertices
                    ))
                ),
                feature_id=item.feature_id,
            )
            for item in room_description.planar_regions
        )
        return self._analysis(
            PropagationSceneSource.DECLARED_PLANAR_SCENE,
            surfaces,
            regions,
            room_geometry,
            room_description,
        )


class RectangularPropagationEngine(PropagationGeometryEngine):
    _ROLE_BY_ID = {
        "front_wall": PlanarSurfaceRole.FRONT_WALL,
        "rear_wall": PlanarSurfaceRole.REAR_WALL,
        "left_wall": PlanarSurfaceRole.LEFT_WALL,
        "right_wall": PlanarSurfaceRole.RIGHT_WALL,
        "floor": PlanarSurfaceRole.FLOOR,
        "ceiling": PlanarSurfaceRole.CEILING,
    }

    def analyze(self, room_geometry, room_description=None):
        if room_geometry is None or room_geometry.source is not GeometrySource.ROOM_DESCRIPTION:
            return PropagationGeometryAnalysis(
                geometry=None,
                missing_fact_codes=("ROOM_DESCRIPTION_GEOMETRY_MISSING",),
                source_analysis_codes=("RoomGeometry",),
                applied_rule_codes=("PROPAGATION_PRESERVE_LEGACY_UNAVAILABLE",),
            )
        dimensions = room_geometry.dimensions
        l, w, h = dimensions.length_m, dimensions.width_m, dimensions.height_m
        vertices = {
            "front_wall": ((0, 0, 0), (0, w, 0), (0, w, h), (0, 0, h)),
            "rear_wall": ((l, 0, 0), (l, 0, h), (l, w, h), (l, w, 0)),
            "left_wall": ((0, 0, 0), (0, 0, h), (l, 0, h), (l, 0, 0)),
            "right_wall": ((0, w, 0), (l, w, 0), (l, w, h), (0, w, h)),
            "floor": ((0, 0, 0), (l, 0, 0), (l, w, 0), (0, w, 0)),
            "ceiling": ((0, 0, h), (0, w, h), (l, w, h), (l, 0, h)),
        }
        surfaces = tuple(
            self._surface(
                surface_id,
                self._ROLE_BY_ID[surface_id],
                tuple(GeometryCoordinate(*point) for point in vertices[surface_id]),
            )
            for surface_id in self._ROLE_BY_ID
        )
        regions = list(self._opening_regions(room_geometry))
        for collection, role, id_field in (
            (room_geometry.covering_zones, PlanarRegionRole.COVERING, "zone_id"),
            (room_geometry.acoustic_treatments, PlanarRegionRole.TREATMENT, "treatment_id"),
        ):
            for item in collection:
                if item.surface_id is None or item.placement is None:
                    continue
                regions.append(PropagationRegion(
                    region_id=getattr(item, id_field),
                    surface_id=item.surface_id,
                    role=role,
                    vertices=self._rectangle_vertices(
                        item.surface_id,
                        item.placement.minimum_corner,
                        item.placement.maximum_corner,
                    ),
                    feature_id=getattr(item, id_field),
                ))
        return self._analysis(
            PropagationSceneSource.RECTANGULAR_ADAPTER,
            surfaces,
            tuple(regions),
            room_geometry,
            room_description,
        )

    @classmethod
    def _opening_regions(cls, geometry):
        dimensions = geometry.dimensions
        for item in geometry.openings:
            horizontal = item.horizontal_offset_m
            vertical = item.vertical_offset_m
            maximum_horizontal = horizontal + item.width_m
            maximum_vertical = vertical + item.height_m
            if item.surface_id == "front_wall":
                values = ((0, horizontal, vertical), (0, maximum_horizontal, vertical), (0, maximum_horizontal, maximum_vertical), (0, horizontal, maximum_vertical))
            elif item.surface_id == "rear_wall":
                values = ((dimensions.length_m, horizontal, vertical), (dimensions.length_m, horizontal, maximum_vertical), (dimensions.length_m, maximum_horizontal, maximum_vertical), (dimensions.length_m, maximum_horizontal, vertical))
            elif item.surface_id == "left_wall":
                values = ((horizontal, 0, vertical), (horizontal, 0, maximum_vertical), (maximum_horizontal, 0, maximum_vertical), (maximum_horizontal, 0, vertical))
            else:
                values = ((horizontal, dimensions.width_m, vertical), (maximum_horizontal, dimensions.width_m, vertical), (maximum_horizontal, dimensions.width_m, maximum_vertical), (horizontal, dimensions.width_m, maximum_vertical))
            yield PropagationRegion(
                item.opening_id, item.surface_id, PlanarRegionRole.OPENING,
                tuple(GeometryCoordinate(*value) for value in values), item.opening_id,
            )

    @staticmethod
    def _rectangle_vertices(surface_id, minimum, maximum):
        x1, y1, z1 = minimum.x_m, minimum.y_m, minimum.z_m
        x2, y2, z2 = maximum.x_m, maximum.y_m, maximum.z_m
        if surface_id in {"front_wall", "rear_wall"}:
            values = ((x1, y1, z1), (x1, y2, z1), (x1, y2, z2), (x1, y1, z2))
        elif surface_id in {"left_wall", "right_wall"}:
            values = ((x1, y1, z1), (x2, y1, z1), (x2, y1, z2), (x1, y1, z2))
        else:
            values = ((x1, y1, z1), (x2, y1, z1), (x2, y2, z1), (x1, y2, z1))
        return tuple(GeometryCoordinate(*value) for value in values)
