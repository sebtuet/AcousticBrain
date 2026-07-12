from dataclasses import dataclass

from .room_description_validation_error import (
    RoomDescriptionValidationCode,
    RoomDescriptionValidationError,
)


@dataclass(frozen=True)
class RoomDescriptionValidationResult:
    """Résultat structuré d'une validation de description de salle."""

    errors: tuple[RoomDescriptionValidationError, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors

    @property
    def error_codes(self) -> tuple[RoomDescriptionValidationCode, ...]:
        return tuple(error.code for error in self.errors)
