import json
from dataclasses import dataclass
from math import isfinite

from acousticbrain.models import (
    ListeningPosition,
    RoomDescription,
    RoomDescriptionLoadResult,
    RoomDescriptionPersistenceError,
    RoomDescriptionPersistenceErrorCode,
    RoomDescriptionPersistenceException,
    RoomDimensions,
    RoomOpening,
    RoomOpeningSurface,
    SpeakerPosition,
)
from acousticbrain.validation import RoomDescriptionValidator


@dataclass(frozen=True)
class _DecodeFailure(Exception):
    code: RoomDescriptionPersistenceErrorCode
    path: tuple[str | int, ...]


class RoomDescriptionJsonCodec:
    """Sérialise le contrat RoomDescription dans une enveloppe versionnée."""

    SCHEMA_VERSION = 1

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
                    }
                    for item in description.speakers
                ],
                "listening_positions": [
                    {
                        "position_id": item.position_id,
                        "x_m": item.x_m,
                        "y_m": item.y_m,
                        "z_m": item.z_m,
                    }
                    for item in description.listening_positions
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
                    for item in description.openings
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
            if version != self.SCHEMA_VERSION or isinstance(version, bool):
                raise _DecodeFailure(
                    RoomDescriptionPersistenceErrorCode.UNKNOWN_SCHEMA_VERSION,
                    ("schema_version",),
                )
            raw = self._mapping(
                self._required(root, "room_description", ()),
                ("room_description",),
            )
            description = self._description(raw)
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
                errors=self._geometry_errors(validation)
            )
        return RoomDescriptionLoadResult(description=description)

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

    def _description(self, raw):
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
                self._speaker(item, index)
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
        )

    def _speaker(self, value, index):
        path = ("room_description", "speakers", index)
        raw = self._mapping(value, path)
        return SpeakerPosition(
            speaker_id=self._string(
                self._required(raw, "speaker_id", path), (*path, "speaker_id")
            ),
            x_m=self._coordinate(raw, "x_m", path),
            y_m=self._coordinate(raw, "y_m", path),
            z_m=self._coordinate(raw, "z_m", path),
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
