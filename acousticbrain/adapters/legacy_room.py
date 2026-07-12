from dataclasses import dataclass
from math import isfinite

from acousticbrain.models import (
    Room,
    RoomDescription,
    RoomDescriptionValidationError,
)
from acousticbrain.validation import RoomDescriptionValidator


@dataclass(frozen=True)
class LegacyRoomAdaptationResult:
    room: Room | None = None
    errors: tuple[RoomDescriptionValidationError, ...] = ()

    @property
    def is_success(self):
        return self.room is not None and not self.errors


class LegacyRoomAdapter:
    """Adapte explicitement RoomDescription vers le modèle Room historique."""

    def __init__(self, validator=None):
        self.validator = validator or RoomDescriptionValidator()

    def adapt(
        self,
        description: RoomDescription,
        *,
        temperature_celsius: float = 20.0,
    ) -> LegacyRoomAdaptationResult:
        if not isinstance(description, RoomDescription):
            raise TypeError("LegacyRoomAdapter requires RoomDescription.")
        if not isfinite(temperature_celsius):
            raise ValueError("Legacy room temperature must be finite.")
        validation = self.validator.validate(description)
        if not validation.is_valid:
            return LegacyRoomAdaptationResult(errors=validation.errors)
        dimensions = description.dimensions
        return LegacyRoomAdaptationResult(
            room=Room(
                name=description.name,
                length=dimensions.length_m,
                width=dimensions.width_m,
                height=dimensions.height_m,
                temperature=temperature_celsius,
            )
        )
