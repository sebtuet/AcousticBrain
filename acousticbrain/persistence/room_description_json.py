import json
from dataclasses import dataclass
from math import isfinite

from acousticbrain.models import (
    AcousticTreatmentDescription,
    AcousticTreatmentType,
    FurnitureType,
    ListeningPosition,
    RoomDescription,
    RoomDescriptionLoadResult,
    RoomDescriptionPersistenceError,
    RoomDescriptionPersistenceErrorCode,
    RoomDescriptionPersistenceException,
    RoomDimensions,
    RoomOpening,
    RoomOpeningSurface,
    RoomDescriptionSurface,
    RoomFurnitureDescription,
    SpeakerPosition,
    SpeakerOrientation,
    SurfaceCoveringZone,
    SurfaceMaterialDescription,
    SurfaceMaterialType,
)
from acousticbrain.validation import RoomDescriptionValidator


@dataclass(frozen=True)
class _DecodeFailure(Exception):
    code: RoomDescriptionPersistenceErrorCode
    path: tuple[str | int, ...]


class RoomDescriptionJsonCodec:
    """Sérialise le contrat RoomDescription dans une enveloppe versionnée."""

    SCHEMA_VERSION = 2
    SUPPORTED_SCHEMA_VERSIONS = (1, 2)

    def __init__(self, validator=None):
        self.validator = validator or RoomDescriptionValidator()

    def dumps(self, description: RoomDescription, *, indent=None) -> str:
        return json.dumps(
            self.to_dict(description),
            indent=indent,
            sort_keys=True,
            allow_nan=False,
        )

    def to_dict(self, description: RoomDescription) -> dict:
        if not isinstance(description, RoomDescription):
            raise TypeError("RoomDescriptionJsonCodec requires RoomDescription.")
        validation = self.validator.validate(description)
        if not validation.is_valid:
            raise RoomDescriptionPersistenceException(
                self._geometry_errors(validation)
            )
        return {
            "schema_version": self.SCHEMA_VERSION,
            "room_description": {
                "name": description.name,
                "dimensions": {
                    "length_m": description.dimensions.length_m,
                    "width_m": description.dimensions.width_m,
                    "height_m": description.dimensions.height_m,
                },
                "speakers": [
                    {
                        "speaker_id": item.speaker_id,
                        "x_m": item.x_m,
                        "y_m": item.y_m,
                        "z_m": item.z_m,
                        "orientation": (
                            {"yaw_degrees": item.orientation.yaw_degrees}
                            if item.orientation is not None
                            else None
                        ),
                    }
                    for item in sorted(
                        description.speakers,
                        key=lambda item: item.speaker_id,
                    )
                ],
                "listening_positions": [
                    {
                        "position_id": item.position_id,
                        "x_m": item.x_m,
                        "y_m": item.y_m,
                        "z_m": item.z_m,
                    }
                    for item in sorted(
                        description.listening_positions,
                        key=lambda item: item.position_id,
                    )
                ],
                "openings": [
                    {
                        "opening_id": item.opening_id,
                        "surface": item.surface.value,
                        "horizontal_offset_m": item.horizontal_offset_m,
                        "vertical_offset_m": item.vertical_offset_m,
                        "width_m": item.width_m,
                        "height_m": item.height_m,
                    }
                    for item in sorted(
                        description.openings,
                        key=lambda item: item.opening_id,
                    )
                ],
                "surface_materials": [
                    {
                        "surface": item.surface.value,
                        "material_type": item.material_type.value,
                        "detail": item.detail,
                    }
                    for item in sorted(
                        description.surface_materials,
                        key=lambda item: item.surface.value,
                    )
                ],
                "covering_zones": [
                    {
                        "zone_id": item.zone_id,
                        "surface": item.surface.value,
                        "material_type": item.material_type.value,
                        "detail": item.detail,
                        "horizontal_offset_m": item.horizontal_offset_m,
                        "vertical_offset_m": item.vertical_offset_m,
                        "width_m": item.width_m,
                        "height_m": item.height_m,
                    }
                    for item in sorted(
                        description.covering_zones,
                        key=lambda item: item.zone_id,
                    )
                ],
                "furniture": [
                    {
                        "furniture_id": item.furniture_id,
                        "furniture_type": item.furniture_type.value,
                        "detail": item.detail,
                        "x_m": item.x_m,
                        "y_m": item.y_m,
                        "z_m": item.z_m,
                        "length_m": item.length_m,
                        "width_m": item.width_m,
                        "height_m": item.height_m,
                    }
                    for item in sorted(
                        description.furniture,
                        key=lambda item: item.furniture_id,
                    )
                ],
                "acoustic_treatments": [
                    {
                        "treatment_id": item.treatment_id,
                        "treatment_type": item.treatment_type.value,
                        "detail": item.detail,
                        "surface": (
                            item.surface.value if item.surface is not None else None
                        ),
                        "horizontal_offset_m": item.horizontal_offset_m,
                        "vertical_offset_m": item.vertical_offset_m,
                        "width_m": item.width_m,
                        "height_m": item.height_m,
                    }
                    for item in sorted(
                        description.acoustic_treatments,
                        key=lambda item: item.treatment_id,
                    )
                ],
            },
        }

    def loads(self, payload: str) -> RoomDescriptionLoadResult:
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            return self._failure(
                RoomDescriptionPersistenceErrorCode.INVALID_JSON,
                (),
            )
        return self.from_dict(data)

    def from_dict(self, data) -> RoomDescriptionLoadResult:
        try:
            root = self._mapping(data, ())
            version = self._required(root, "schema_version", ())
            if (
                version not in self.SUPPORTED_SCHEMA_VERSIONS
                or isinstance(version, bool)
            ):
                raise _DecodeFailure(
                    RoomDescriptionPersistenceErrorCode.UNKNOWN_SCHEMA_VERSION,
                    ("schema_version",),
                )
            raw = self._mapping(
                self._required(root, "room_description", ()),
                ("room_description",),
            )
            description = self._description(raw, version)
        except _DecodeFailure as failure:
            return self._failure(failure.code, failure.path)
        except (TypeError, ValueError):
            return self._failure(
                RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
                ("room_description",),
            )

        validation = self.validator.validate(description)
        if not validation.is_valid:
            return RoomDescriptionLoadResult(
                errors=self._geometry_errors(validation),
                source_schema_version=version,
            )
        return RoomDescriptionLoadResult(
            description=description,
            source_schema_version=version,
            requires_migration=version < self.SCHEMA_VERSION,
        )

    @staticmethod
    def _geometry_errors(validation):
        return tuple(
            RoomDescriptionPersistenceError(
                code=RoomDescriptionPersistenceErrorCode.INVALID_GEOMETRY,
                path=(
                    "room_description",
                    error.entity_type.value.lower(),
                    *error.entity_ids,
                ),
                validation_code=error.code,
                entity_ids=error.entity_ids,
            )
            for error in validation.errors
        )

    def _description(self, raw, version):
        base = ("room_description",)
        dimensions_raw = self._mapping(
            self._required(raw, "dimensions", base),
            (*base, "dimensions"),
        )
        dimensions = RoomDimensions(
            length_m=self._positive_number(
                self._required(dimensions_raw, "length_m", (*base, "dimensions")),
                (*base, "dimensions", "length_m"),
            ),
            width_m=self._positive_number(
                self._required(dimensions_raw, "width_m", (*base, "dimensions")),
                (*base, "dimensions", "width_m"),
            ),
            height_m=self._positive_number(
                self._required(dimensions_raw, "height_m", (*base, "dimensions")),
                (*base, "dimensions", "height_m"),
            ),
        )
        return RoomDescription(
            name=self._string(self._required(raw, "name", base), (*base, "name")),
            dimensions=dimensions,
            speakers=tuple(
                self._speaker(item, index, version)
                for index, item in enumerate(
                    self._sequence(
                        self._required(raw, "speakers", base),
                        (*base, "speakers"),
                    )
                )
            ),
            listening_positions=tuple(
                self._listening_position(item, index)
                for index, item in enumerate(
                    self._sequence(
                        self._required(raw, "listening_positions", base),
                        (*base, "listening_positions"),
                    )
                )
            ),
            openings=tuple(
                self._opening(item, index)
                for index, item in enumerate(
                    self._sequence(
                        self._required(raw, "openings", base),
                        (*base, "openings"),
                    )
                )
            ),
            surface_materials=tuple(
                self._surface_material(item, index)
                for index, item in enumerate(
                    self._optional_sequence(raw, "surface_materials", base)
                )
            ),
            covering_zones=tuple(
                self._covering_zone(item, index)
                for index, item in enumerate(
                    self._optional_sequence(raw, "covering_zones", base)
                )
            ),
            furniture=tuple(
                self._furniture(item, index)
                for index, item in enumerate(
                    self._optional_sequence(raw, "furniture", base)
                )
            ),
            acoustic_treatments=tuple(
                self._treatment(item, index)
                for index, item in enumerate(
                    self._optional_sequence(raw, "acoustic_treatments", base)
                )
            ),
        )

    def _speaker(self, value, index, version):
        path = ("room_description", "speakers", index)
        raw = self._mapping(value, path)
        orientation_value = raw.get("orientation") if version >= 2 else None
        orientation = None
        if orientation_value is not None:
            orientation_path = (*path, "orientation")
            orientation_raw = self._mapping(orientation_value, orientation_path)
            orientation = SpeakerOrientation(
                yaw_degrees=self._yaw(
                    self._required(
                        orientation_raw,
                        "yaw_degrees",
                        orientation_path,
                    ),
                    (*orientation_path, "yaw_degrees"),
                )
            )
        return SpeakerPosition(
            speaker_id=self._string(
                self._required(raw, "speaker_id", path), (*path, "speaker_id")
            ),
            x_m=self._coordinate(raw, "x_m", path),
            y_m=self._coordinate(raw, "y_m", path),
            z_m=self._coordinate(raw, "z_m", path),
            orientation=orientation,
        )

    def _listening_position(self, value, index):
        path = ("room_description", "listening_positions", index)
        raw = self._mapping(value, path)
        return ListeningPosition(
            position_id=self._string(
                self._required(raw, "position_id", path),
                (*path, "position_id"),
            ),
            x_m=self._coordinate(raw, "x_m", path),
            y_m=self._coordinate(raw, "y_m", path),
            z_m=self._coordinate(raw, "z_m", path),
        )

    def _opening(self, value, index):
        path = ("room_description", "openings", index)
        raw = self._mapping(value, path)
        surface_path = (*path, "surface")
        surface_value = self._string(
            self._required(raw, "surface", path), surface_path
        )
        try:
            surface = RoomOpeningSurface(surface_value)
        except ValueError:
            raise _DecodeFailure(
                RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
                surface_path,
            )
        return RoomOpening(
            opening_id=self._string(
                self._required(raw, "opening_id", path),
                (*path, "opening_id"),
            ),
            surface=surface,
            horizontal_offset_m=self._coordinate(
                raw, "horizontal_offset_m", path
            ),
            vertical_offset_m=self._coordinate(
                raw, "vertical_offset_m", path
            ),
            width_m=self._positive_number(
                self._required(raw, "width_m", path), (*path, "width_m")
            ),
            height_m=self._positive_number(
                self._required(raw, "height_m", path), (*path, "height_m")
            ),
        )

    def _surface_material(self, value, index):
        path = ("room_description", "surface_materials", index)
        raw = self._mapping(value, path)
        return SurfaceMaterialDescription(
            surface=self._enum(
                RoomDescriptionSurface,
                self._required(raw, "surface", path),
                (*path, "surface"),
            ),
            material_type=self._enum(
                SurfaceMaterialType,
                self._required(raw, "material_type", path),
                (*path, "material_type"),
            ),
            detail=self._nullable_string(raw.get("detail"), (*path, "detail")),
        )

    def _covering_zone(self, value, index):
        path = ("room_description", "covering_zones", index)
        raw = self._mapping(value, path)
        return SurfaceCoveringZone(
            zone_id=self._string(
                self._required(raw, "zone_id", path), (*path, "zone_id")
            ),
            surface=self._enum(
                RoomDescriptionSurface,
                self._required(raw, "surface", path),
                (*path, "surface"),
            ),
            material_type=self._enum(
                SurfaceMaterialType,
                self._required(raw, "material_type", path),
                (*path, "material_type"),
            ),
            detail=self._nullable_string(raw.get("detail"), (*path, "detail")),
            horizontal_offset_m=self._nullable_coordinate(
                raw.get("horizontal_offset_m"),
                (*path, "horizontal_offset_m"),
            ),
            vertical_offset_m=self._nullable_coordinate(
                raw.get("vertical_offset_m"),
                (*path, "vertical_offset_m"),
            ),
            width_m=self._nullable_positive_number(
                raw.get("width_m"), (*path, "width_m")
            ),
            height_m=self._nullable_positive_number(
                raw.get("height_m"), (*path, "height_m")
            ),
        )

    def _furniture(self, value, index):
        path = ("room_description", "furniture", index)
        raw = self._mapping(value, path)
        return RoomFurnitureDescription(
            furniture_id=self._string(
                self._required(raw, "furniture_id", path),
                (*path, "furniture_id"),
            ),
            furniture_type=self._enum(
                FurnitureType,
                self._required(raw, "furniture_type", path),
                (*path, "furniture_type"),
            ),
            detail=self._nullable_string(raw.get("detail"), (*path, "detail")),
            x_m=self._nullable_coordinate(raw.get("x_m"), (*path, "x_m")),
            y_m=self._nullable_coordinate(raw.get("y_m"), (*path, "y_m")),
            z_m=self._nullable_coordinate(raw.get("z_m"), (*path, "z_m")),
            length_m=self._nullable_positive_number(
                raw.get("length_m"), (*path, "length_m")
            ),
            width_m=self._nullable_positive_number(
                raw.get("width_m"), (*path, "width_m")
            ),
            height_m=self._nullable_positive_number(
                raw.get("height_m"), (*path, "height_m")
            ),
        )

    def _treatment(self, value, index):
        path = ("room_description", "acoustic_treatments", index)
        raw = self._mapping(value, path)
        raw_surface = raw.get("surface")
        surface = (
            None
            if raw_surface is None
            else self._enum(
                RoomDescriptionSurface,
                raw_surface,
                (*path, "surface"),
            )
        )
        return AcousticTreatmentDescription(
            treatment_id=self._string(
                self._required(raw, "treatment_id", path),
                (*path, "treatment_id"),
            ),
            treatment_type=self._enum(
                AcousticTreatmentType,
                self._required(raw, "treatment_type", path),
                (*path, "treatment_type"),
            ),
            detail=self._nullable_string(raw.get("detail"), (*path, "detail")),
            surface=surface,
            horizontal_offset_m=self._nullable_coordinate(
                raw.get("horizontal_offset_m"),
                (*path, "horizontal_offset_m"),
            ),
            vertical_offset_m=self._nullable_coordinate(
                raw.get("vertical_offset_m"),
                (*path, "vertical_offset_m"),
            ),
            width_m=self._nullable_positive_number(
                raw.get("width_m"), (*path, "width_m")
            ),
            height_m=self._nullable_positive_number(
                raw.get("height_m"), (*path, "height_m")
            ),
        )

    def _coordinate(self, raw, field, path):
        value = self._number(
            self._required(raw, field, path),
            (*path, field),
        )
        if value < 0.0:
            raise _DecodeFailure(
                RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
                (*path, field),
            )
        return value

    def _nullable_coordinate(self, value, path):
        if value is None:
            return None
        number = self._number(value, path)
        if number < 0.0:
            raise _DecodeFailure(
                RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
                path,
            )
        return number

    @classmethod
    def _yaw(cls, value, path):
        number = cls._number(value, path)
        if not -180.0 <= number <= 180.0:
            raise _DecodeFailure(
                RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
                path,
            )
        return number

    @classmethod
    def _nullable_positive_number(cls, value, path):
        if value is None:
            return None
        return cls._positive_number(value, path)

    @classmethod
    def _nullable_string(cls, value, path):
        if value is None:
            return None
        return cls._string(value, path)

    @classmethod
    def _enum(cls, enum_type, value, path):
        raw = cls._string(value, path)
        try:
            return enum_type(raw)
        except ValueError:
            raise _DecodeFailure(
                RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
                path,
            )

    @classmethod
    def _positive_number(cls, value, path):
        number = cls._number(value, path)
        if number <= 0.0:
            raise _DecodeFailure(
                RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
                path,
            )
        return number

    @staticmethod
    def _required(mapping, field, path):
        if field not in mapping:
            raise _DecodeFailure(
                RoomDescriptionPersistenceErrorCode.MISSING_FIELD,
                (*path, field),
            )
        return mapping[field]

    @staticmethod
    def _mapping(value, path):
        if not isinstance(value, dict):
            raise _DecodeFailure(
                RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
                path,
            )
        return value

    @staticmethod
    def _sequence(value, path):
        if not isinstance(value, list):
            raise _DecodeFailure(
                RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
                path,
            )
        return value

    @classmethod
    def _optional_sequence(cls, mapping, field, path):
        if field not in mapping:
            return []
        return cls._sequence(mapping[field], (*path, field))

    @staticmethod
    def _number(value, path):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
        ):
            raise _DecodeFailure(
                RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
                path,
            )
        return float(value)

    @staticmethod
    def _string(value, path):
        if not isinstance(value, str) or not value.strip():
            raise _DecodeFailure(
                RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
                path,
            )
        return value

    @staticmethod
    def _failure(code, path):
        return RoomDescriptionLoadResult(
            errors=(RoomDescriptionPersistenceError(code=code, path=path),)
        )
