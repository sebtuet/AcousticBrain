from dataclasses import dataclass
from pathlib import Path

from acousticbrain.models import (
    RoomDescriptionPersistenceError,
    RoomDescriptionPersistenceErrorCode,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec
from acousticbrain.project import Project


@dataclass(frozen=True)
class RoomDescriptionProjectLoadResult:
    attached: bool = False
    errors: tuple[RoomDescriptionPersistenceError, ...] = ()
    source_schema_version: int | None = None
    requires_migration: bool = False

    @property
    def is_success(self) -> bool:
        return self.attached and not self.errors


class RoomDescriptionProjectLoader:
    """Charge explicitement un fichier validé dans un Project existant."""

    def __init__(self, codec=None):
        self.codec = codec or RoomDescriptionJsonCodec()

    def load(self, project: Project, path) -> RoomDescriptionProjectLoadResult:
        if not isinstance(project, Project):
            raise TypeError("Room-description loading requires Project.")
        source = Path(path)
        try:
            payload = source.read_text(encoding="utf-8")
        except FileNotFoundError:
            return self._failure(
                RoomDescriptionPersistenceErrorCode.FILE_NOT_FOUND,
                source,
            )
        except (OSError, UnicodeError):
            return self._failure(
                RoomDescriptionPersistenceErrorCode.FILE_READ_ERROR,
                source,
            )

        loaded = self.codec.loads(payload)
        if not loaded.is_success:
            return RoomDescriptionProjectLoadResult(errors=loaded.errors)

        project.room_description = loaded.description
        return RoomDescriptionProjectLoadResult(
            attached=True,
            source_schema_version=loaded.source_schema_version,
            requires_migration=loaded.requires_migration,
        )

    @staticmethod
    def _failure(code, path):
        return RoomDescriptionProjectLoadResult(
            errors=(
                RoomDescriptionPersistenceError(
                    code=code,
                    path=(str(path),),
                ),
            )
        )
