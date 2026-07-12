from dataclasses import dataclass
from enum import Enum


class RoomDescriptionValidationCode(Enum):
    """Codes stables de validation géométrique relationnelle."""

    SPEAKER_OUTSIDE_ROOM = "SPEAKER_OUTSIDE_ROOM"
    LISTENING_POSITION_OUTSIDE_ROOM = "LISTENING_POSITION_OUTSIDE_ROOM"
    OPENING_OUTSIDE_SURFACE = "OPENING_OUTSIDE_SURFACE"
    OPENING_ZERO_AREA = "OPENING_ZERO_AREA"
    OPENING_OVERLAP = "OPENING_OVERLAP"


class RoomDescriptionEntityType(Enum):
    SPEAKER = "SPEAKER"
    LISTENING_POSITION = "LISTENING_POSITION"
    OPENING = "OPENING"


@dataclass(frozen=True)
class RoomDescriptionValidationError:
    """Erreur géométrique structurée, sans texte d'interface."""

    code: RoomDescriptionValidationCode
    entity_type: RoomDescriptionEntityType
    entity_ids: tuple[str, ...]
    fields: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.entity_ids:
            raise ValueError("A validation error requires an entity identifier.")
        if len(self.entity_ids) != len(set(self.entity_ids)):
            raise ValueError("Validation-error entity identifiers must be unique.")
