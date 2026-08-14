from dataclasses import dataclass
from enum import Enum

from .room_description import RoomDescription
from .room_description_validation_error import RoomDescriptionValidationCode


class RoomDescriptionPersistenceErrorCode(Enum):
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_READ_ERROR = "FILE_READ_ERROR"
    INVALID_JSON = "INVALID_JSON"
    UNKNOWN_SCHEMA_VERSION = "UNKNOWN_SCHEMA_VERSION"
    EDITOR_UNSUPPORTED_FREQUENCY_MATERIALS = "EDITOR_UNSUPPORTED_FREQUENCY_MATERIALS"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_VALUE = "INVALID_VALUE"
    INVALID_GEOMETRY = "INVALID_GEOMETRY"
    EDITOR_UNSUPPORTED_PLANAR_GEOMETRY = "EDITOR_UNSUPPORTED_PLANAR_GEOMETRY"


@dataclass(frozen=True)
class RoomDescriptionPersistenceError:
    """Erreur structurée de persistance, indépendante de l'interface."""

    code: RoomDescriptionPersistenceErrorCode
    path: tuple[str | int, ...] = ()
    validation_code: RoomDescriptionValidationCode | None = None
    entity_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RoomDescriptionLoadResult:
    """Résultat déterministe d'une désérialisation JSON."""

    description: RoomDescription | None = None
    errors: tuple[RoomDescriptionPersistenceError, ...] = ()
    source_schema_version: int | None = None
    requires_migration: bool = False

    def __post_init__(self):
        if self.description is not None and self.errors:
            raise ValueError("A load result cannot contain data and errors.")
        if self.requires_migration and (
            self.description is None or self.source_schema_version is None
        ):
            raise ValueError(
                "Migration status requires loaded data and a source version."
            )

    @property
    def is_success(self) -> bool:
        return self.description is not None and not self.errors


class RoomDescriptionPersistenceException(Exception):
    """Échec de sérialisation portant uniquement des erreurs structurées."""

    def __init__(self, errors: tuple[RoomDescriptionPersistenceError, ...]):
        self.errors = errors
        super().__init__(*errors)
