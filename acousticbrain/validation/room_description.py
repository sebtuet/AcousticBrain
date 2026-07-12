from itertools import combinations

from acousticbrain.models import (
    RoomDescription,
    RoomDescriptionEntityType,
    RoomDescriptionValidationCode,
    RoomDescriptionValidationError,
    RoomDescriptionValidationResult,
    RoomOpeningSurface,
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

        return RoomDescriptionValidationResult(errors=tuple(errors))

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
