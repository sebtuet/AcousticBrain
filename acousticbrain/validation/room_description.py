from itertools import combinations
from math import isfinite

from acousticbrain.models import (
    PlanarRegionRole,
    RoomDescription,
    RoomDescriptionEntityType,
    RoomDescriptionValidationCode,
    RoomDescriptionValidationError,
    RoomDescriptionValidationResult,
    RoomOpeningSurface,
    RoomDescriptionSurface,
)
from acousticbrain.geometry import (
    PLANAR_TOLERANCE_M,
    derive_planar_basis,
    point_in_convex_polygon,
    polygon_is_convex,
    project_point,
)


class RoomDescriptionValidator:
    """Valide les relations géométriques d'une description utilisateur."""

    def validate(
        self,
        description: RoomDescription,
    ) -> RoomDescriptionValidationResult:
        if not isinstance(description, RoomDescription):
            raise TypeError("RoomDescriptionValidator requires RoomDescription.")

        errors = []
        dimensions = description.dimensions
        bounds = (dimensions.length_m, dimensions.width_m, dimensions.height_m)

        for speaker in sorted(
            description.speakers, key=lambda item: item.speaker_id
        ):
            fields = self._outside_coordinate_fields(speaker, bounds)
            if fields:
                errors.append(
                    self._error(
                        RoomDescriptionValidationCode.SPEAKER_OUTSIDE_ROOM,
                        RoomDescriptionEntityType.SPEAKER,
                        (speaker.speaker_id,),
                        fields,
                    )
                )

        for position in sorted(
            description.listening_positions,
            key=lambda item: item.position_id,
        ):
            fields = self._outside_coordinate_fields(position, bounds)
            if fields:
                errors.append(
                    self._error(
                        RoomDescriptionValidationCode.LISTENING_POSITION_OUTSIDE_ROOM,
                        RoomDescriptionEntityType.LISTENING_POSITION,
                        (position.position_id,),
                        fields,
                    )
                )

        openings = sorted(
            description.openings, key=lambda item: item.opening_id
        )
        for opening in openings:
            if opening.width_m <= 0.0 or opening.height_m <= 0.0:
                fields = tuple(
                    field
                    for field, value in (
                        ("width_m", opening.width_m),
                        ("height_m", opening.height_m),
                    )
                    if value <= 0.0
                )
                errors.append(
                    self._error(
                        RoomDescriptionValidationCode.OPENING_ZERO_AREA,
                        RoomDescriptionEntityType.OPENING,
                        (opening.opening_id,),
                        fields,
                    )
                )
                continue

            fields = self._opening_outside_fields(opening, dimensions)
            if fields:
                errors.append(
                    self._error(
                        RoomDescriptionValidationCode.OPENING_OUTSIDE_SURFACE,
                        RoomDescriptionEntityType.OPENING,
                        (opening.opening_id,),
                        fields,
                    )
                )

        for first, second in combinations(openings, 2):
            if first.surface is not second.surface:
                continue
            if self._openings_overlap(first, second):
                errors.append(
                    self._error(
                        RoomDescriptionValidationCode.OPENING_OVERLAP,
                        RoomDescriptionEntityType.OPENING,
                        (first.opening_id, second.opening_id),
                        (
                            "horizontal_offset_m",
                            "vertical_offset_m",
                            "width_m",
                            "height_m",
                        ),
                    )
                )

        zones = sorted(
            description.covering_zones, key=lambda item: item.zone_id
        )
        valid_zones = []
        for zone in zones:
            state = self._rectangle_placement_state(zone)
            if not isinstance(zone.surface, RoomDescriptionSurface):
                state = "INVALID"
            if state == "ABSENT":
                continue
            if state == "INVALID":
                errors.append(
                    self._feature_placement_error(
                        RoomDescriptionEntityType.COVERING_ZONE,
                        zone.zone_id,
                        self._rectangle_fields(),
                    )
                )
                continue
            fields = self._surface_rectangle_outside_fields(
                zone, dimensions
            )
            if fields:
                errors.append(
                    self._error(
                        RoomDescriptionValidationCode.COVERING_ZONE_OUTSIDE_SURFACE,
                        RoomDescriptionEntityType.COVERING_ZONE,
                        (zone.zone_id,),
                        fields,
                    )
                )
            else:
                valid_zones.append(zone)
        errors.extend(
            self._surface_overlap_errors(
                valid_zones,
                id_attribute="zone_id",
                code=RoomDescriptionValidationCode.COVERING_ZONE_OVERLAP,
                entity_type=RoomDescriptionEntityType.COVERING_ZONE,
            )
        )

        furniture = sorted(
            description.furniture, key=lambda item: item.furniture_id
        )
        valid_furniture = []
        for item in furniture:
            state = self._furniture_placement_state(item)
            if state == "ABSENT":
                continue
            if state == "INVALID":
                errors.append(
                    self._feature_placement_error(
                        RoomDescriptionEntityType.FURNITURE,
                        item.furniture_id,
                        self._furniture_fields(),
                    )
                )
                continue
            fields = self._furniture_outside_fields(item, dimensions)
            if fields:
                errors.append(
                    self._error(
                        RoomDescriptionValidationCode.FURNITURE_OUTSIDE_ROOM,
                        RoomDescriptionEntityType.FURNITURE,
                        (item.furniture_id,),
                        fields,
                    )
                )
            else:
                valid_furniture.append(item)
        errors.extend(self._furniture_overlap_errors(valid_furniture))

        treatments = sorted(
            description.acoustic_treatments,
            key=lambda item: item.treatment_id,
        )
        valid_treatments = []
        for treatment in treatments:
            state = self._treatment_placement_state(treatment)
            if state == "ABSENT":
                continue
            if state == "INVALID":
                errors.append(
                    self._feature_placement_error(
                        RoomDescriptionEntityType.ACOUSTIC_TREATMENT,
                        treatment.treatment_id,
                        ("surface", *self._rectangle_fields()),
                    )
                )
                continue
            fields = self._surface_rectangle_outside_fields(
                treatment, dimensions
            )
            if fields:
                errors.append(
                    self._error(
                        RoomDescriptionValidationCode.TREATMENT_OUTSIDE_SURFACE,
                        RoomDescriptionEntityType.ACOUSTIC_TREATMENT,
                        (treatment.treatment_id,),
                        fields,
                    )
                )
            else:
                valid_treatments.append(treatment)
        errors.extend(
            self._surface_overlap_errors(
                valid_treatments,
                id_attribute="treatment_id",
                code=RoomDescriptionValidationCode.TREATMENT_OVERLAP,
                entity_type=RoomDescriptionEntityType.ACOUSTIC_TREATMENT,
            )
        )

        errors.extend(self._planar_errors(description))

        return RoomDescriptionValidationResult(errors=tuple(errors))

    @classmethod
    def _planar_errors(cls, description):
        errors = []
        surfaces = {}
        for surface in sorted(
            description.planar_surfaces, key=lambda item: item.surface_id
        ):
            try:
                basis = derive_planar_basis(surface.vertices)
                polygon = tuple(project_point(item, basis)[:2] for item in surface.vertices)
                if not polygon_is_convex(polygon):
                    raise ValueError("Polygon is not convex.")
            except ValueError:
                errors.append(cls._error(
                    RoomDescriptionValidationCode.PLANAR_SURFACE_INVALID_POLYGON,
                    RoomDescriptionEntityType.PLANAR_SURFACE,
                    (surface.surface_id,),
                    ("vertices",),
                ))
                continue
            surfaces[surface.surface_id] = (surface, basis, polygon)

        feature_ids = {
            PlanarRegionRole.COVERING: {
                item.zone_id: item for item in description.covering_zones
            },
            PlanarRegionRole.TREATMENT: {
                item.treatment_id: item for item in description.acoustic_treatments
            },
            PlanarRegionRole.OPENING: {
                item.opening_id: item for item in description.openings
            },
        }
        for region in sorted(
            description.planar_regions, key=lambda item: item.region_id
        ):
            resolved = surfaces.get(region.surface_id)
            if resolved is None:
                errors.append(cls._error(
                    RoomDescriptionValidationCode.PLANAR_REGION_UNKNOWN_SURFACE,
                    RoomDescriptionEntityType.PLANAR_REGION,
                    (region.region_id,),
                    ("surface_id",),
                ))
                continue
            _, basis, surface_polygon = resolved
            projected = tuple(project_point(item, basis) for item in region.vertices)
            if any(abs(item[2]) > PLANAR_TOLERANCE_M for item in projected):
                errors.append(cls._error(
                    RoomDescriptionValidationCode.PLANAR_REGION_NOT_COPLANAR,
                    RoomDescriptionEntityType.PLANAR_REGION,
                    (region.region_id,),
                    ("vertices",),
                ))
                continue
            region_polygon = tuple(item[:2] for item in projected)
            if not polygon_is_convex(region_polygon) or any(
                not point_in_convex_polygon(point, surface_polygon)
                for point in region_polygon
            ):
                errors.append(cls._error(
                    RoomDescriptionValidationCode.PLANAR_REGION_OUTSIDE_SURFACE,
                    RoomDescriptionEntityType.PLANAR_REGION,
                    (region.region_id,),
                    ("vertices",),
                ))
            if region.feature_id is None:
                continue
            feature = feature_ids[region.role].get(region.feature_id)
            if feature is None:
                errors.append(cls._error(
                    RoomDescriptionValidationCode.PLANAR_REGION_UNKNOWN_FEATURE,
                    RoomDescriptionEntityType.PLANAR_REGION,
                    (region.region_id,),
                    ("feature_id",),
                ))
            elif cls._feature_has_legacy_placement(region.role, feature):
                errors.append(cls._error(
                    RoomDescriptionValidationCode.PLANAR_REGION_PLACEMENT_CONFLICT,
                    RoomDescriptionEntityType.PLANAR_REGION,
                    (region.region_id,),
                    ("feature_id",),
                ))
        return errors

    @staticmethod
    def _feature_has_legacy_placement(role, feature):
        if role is PlanarRegionRole.OPENING:
            return True
        return getattr(feature, "horizontal_offset_m", None) is not None

    @staticmethod
    def _rectangle_fields():
        return (
            "horizontal_offset_m",
            "vertical_offset_m",
            "width_m",
            "height_m",
        )

    @staticmethod
    def _furniture_fields():
        return ("x_m", "y_m", "z_m", "length_m", "width_m", "height_m")

    @classmethod
    def _rectangle_placement_state(cls, item):
        values = tuple(getattr(item, field) for field in cls._rectangle_fields())
        if all(value is None for value in values):
            return "ABSENT"
        if any(value is None for value in values):
            return "INVALID"
        if not cls._finite_numbers(values):
            return "INVALID"
        if min(values[:2]) < 0.0 or min(values[2:]) <= 0.0:
            return "INVALID"
        return "VALID"

    @classmethod
    def _furniture_placement_state(cls, item):
        values = tuple(getattr(item, field) for field in cls._furniture_fields())
        if all(value is None for value in values):
            return "ABSENT"
        if any(value is None for value in values):
            return "INVALID"
        if not cls._finite_numbers(values):
            return "INVALID"
        if min(values[:3]) < 0.0 or min(values[3:]) <= 0.0:
            return "INVALID"
        return "VALID"

    @classmethod
    def _treatment_placement_state(cls, item):
        rectangle_state = cls._rectangle_placement_state(item)
        if item.surface is None and rectangle_state == "ABSENT":
            return "ABSENT"
        if not isinstance(item.surface, RoomDescriptionSurface):
            return "INVALID"
        return rectangle_state if rectangle_state != "ABSENT" else "INVALID"

    @staticmethod
    def _finite_numbers(values):
        return all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            for value in values
        )

    @staticmethod
    def _surface_limits(surface, dimensions):
        if surface in {
            RoomDescriptionSurface.FRONT_WALL,
            RoomDescriptionSurface.REAR_WALL,
        }:
            return dimensions.width_m, dimensions.height_m
        if surface in {
            RoomDescriptionSurface.LEFT_WALL,
            RoomDescriptionSurface.RIGHT_WALL,
        }:
            return dimensions.length_m, dimensions.height_m
        return dimensions.length_m, dimensions.width_m

    @classmethod
    def _surface_rectangle_outside_fields(cls, item, dimensions):
        horizontal_limit, vertical_limit = cls._surface_limits(
            item.surface, dimensions
        )
        fields = []
        if item.horizontal_offset_m + item.width_m > horizontal_limit:
            fields.extend(("horizontal_offset_m", "width_m"))
        if item.vertical_offset_m + item.height_m > vertical_limit:
            fields.extend(("vertical_offset_m", "height_m"))
        return tuple(fields)

    @staticmethod
    def _furniture_outside_fields(item, dimensions):
        fields = []
        if item.x_m + item.length_m > dimensions.length_m:
            fields.extend(("x_m", "length_m"))
        if item.y_m + item.width_m > dimensions.width_m:
            fields.extend(("y_m", "width_m"))
        if item.z_m + item.height_m > dimensions.height_m:
            fields.extend(("z_m", "height_m"))
        return tuple(fields)

    @classmethod
    def _surface_overlap_errors(
        cls, items, *, id_attribute, code, entity_type
    ):
        errors = []
        for first, second in combinations(items, 2):
            if first.surface is not second.surface:
                continue
            if cls._rectangles_overlap(first, second):
                errors.append(
                    cls._error(
                        code,
                        entity_type,
                        (
                            getattr(first, id_attribute),
                            getattr(second, id_attribute),
                        ),
                        cls._rectangle_fields(),
                    )
                )
        return errors

    @staticmethod
    def _rectangles_overlap(first, second):
        return (
            max(first.horizontal_offset_m, second.horizontal_offset_m)
            < min(
                first.horizontal_offset_m + first.width_m,
                second.horizontal_offset_m + second.width_m,
            )
            and max(first.vertical_offset_m, second.vertical_offset_m)
            < min(
                first.vertical_offset_m + first.height_m,
                second.vertical_offset_m + second.height_m,
            )
        )

    @classmethod
    def _furniture_overlap_errors(cls, items):
        errors = []
        for first, second in combinations(items, 2):
            if cls._boxes_overlap(first, second):
                errors.append(
                    cls._error(
                        RoomDescriptionValidationCode.FURNITURE_OVERLAP,
                        RoomDescriptionEntityType.FURNITURE,
                        (first.furniture_id, second.furniture_id),
                        cls._furniture_fields(),
                    )
                )
        return errors

    @staticmethod
    def _boxes_overlap(first, second):
        return all(
            max(first_start, second_start)
            < min(first_start + first_size, second_start + second_size)
            for first_start, first_size, second_start, second_size in (
                (first.x_m, first.length_m, second.x_m, second.length_m),
                (first.y_m, first.width_m, second.y_m, second.width_m),
                (first.z_m, first.height_m, second.z_m, second.height_m),
            )
        )

    @classmethod
    def _feature_placement_error(cls, entity_type, entity_id, fields):
        return cls._error(
            RoomDescriptionValidationCode.INVALID_FEATURE_PLACEMENT,
            entity_type,
            (entity_id,),
            tuple(fields),
        )

    @staticmethod
    def _outside_coordinate_fields(position, bounds):
        return tuple(
            field
            for field, value, maximum in zip(
                ("x_m", "y_m", "z_m"),
                (position.x_m, position.y_m, position.z_m),
                bounds,
            )
            if not 0.0 <= value <= maximum
        )

    @staticmethod
    def _opening_outside_fields(opening, dimensions):
        horizontal_limit = (
            dimensions.width_m
            if opening.surface
            in {
                RoomOpeningSurface.FRONT_WALL,
                RoomOpeningSurface.REAR_WALL,
            }
            else dimensions.length_m
        )
        fields = []
        if (
            opening.horizontal_offset_m < 0.0
            or opening.horizontal_offset_m + opening.width_m
            > horizontal_limit
        ):
            fields.extend(("horizontal_offset_m", "width_m"))
        if (
            opening.vertical_offset_m < 0.0
            or opening.vertical_offset_m + opening.height_m
            > dimensions.height_m
        ):
            fields.extend(("vertical_offset_m", "height_m"))
        return tuple(fields)

    @staticmethod
    def _openings_overlap(first, second):
        horizontal_overlap = max(
            first.horizontal_offset_m,
            second.horizontal_offset_m,
        ) < min(
            first.horizontal_offset_m + first.width_m,
            second.horizontal_offset_m + second.width_m,
        )
        vertical_overlap = max(
            first.vertical_offset_m,
            second.vertical_offset_m,
        ) < min(
            first.vertical_offset_m + first.height_m,
            second.vertical_offset_m + second.height_m,
        )
        return horizontal_overlap and vertical_overlap

    @staticmethod
    def _error(code, entity_type, entity_ids, fields):
        return RoomDescriptionValidationError(
            code=code,
            entity_type=entity_type,
            entity_ids=entity_ids,
            fields=tuple(fields),
        )
