from dataclasses import dataclass
from enum import Enum


class RoomDescriptionValidationCode(Enum):
    """Codes stables de validation géométrique relationnelle."""

    SPEAKER_OUTSIDE_ROOM = "SPEAKER_OUTSIDE_ROOM"
    LISTENING_POSITION_OUTSIDE_ROOM = "LISTENING_POSITION_OUTSIDE_ROOM"
    OPENING_OUTSIDE_SURFACE = "OPENING_OUTSIDE_SURFACE"
    OPENING_ZERO_AREA = "OPENING_ZERO_AREA"
    OPENING_OVERLAP = "OPENING_OVERLAP"
    COVERING_ZONE_OUTSIDE_SURFACE = "COVERING_ZONE_OUTSIDE_SURFACE"
    COVERING_ZONE_OVERLAP = "COVERING_ZONE_OVERLAP"
    FURNITURE_OUTSIDE_ROOM = "FURNITURE_OUTSIDE_ROOM"
    FURNITURE_OVERLAP = "FURNITURE_OVERLAP"
    TREATMENT_OUTSIDE_SURFACE = "TREATMENT_OUTSIDE_SURFACE"
    TREATMENT_OVERLAP = "TREATMENT_OVERLAP"
    INVALID_FEATURE_PLACEMENT = "INVALID_FEATURE_PLACEMENT"


class RoomDescriptionEntityType(Enum):
    SPEAKER = "SPEAKER"
    LISTENING_POSITION = "LISTENING_POSITION"
    OPENING = "OPENING"
    COVERING_ZONE = "COVERING_ZONE"
    FURNITURE = "FURNITURE"
    ACOUSTIC_TREATMENT = "ACOUSTIC_TREATMENT"


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
