from dataclasses import dataclass

from .room_description import RoomDescription


@dataclass(frozen=True)
class SBIRRoomGeometryDeclarationInput:
    schema_version: int
    declaration_input_id: str
    target_experiment_id: str
    declaration_source: str
    room_description: RoomDescription
    user_note: str | None

    CURRENT_SCHEMA_VERSION = 1
    TARGET_EXPERIMENT_ID = "baseline"
    DECLARATION_SOURCE = "USER_MEASUREMENT"

    def __post_init__(self):
        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
            or self.schema_version != self.CURRENT_SCHEMA_VERSION
        ):
            raise ValueError("Unsupported SBIR room-geometry input schema version.")
        for field, value in (
            ("declaration_input_id", self.declaration_input_id),
            ("target_experiment_id", self.target_experiment_id),
            ("declaration_source", self.declaration_source),
        ):
            if not isinstance(value, str):
                raise TypeError(
                    f"SBIR room-geometry field {field} must be a string."
                )
            if not value or value != value.strip():
                raise ValueError(
                    f"SBIR room-geometry field {field} must be exact non-empty text."
                )
        if self.target_experiment_id != self.TARGET_EXPERIMENT_ID:
            raise ValueError(
                "SBIR room-geometry target_experiment_id must be exactly baseline."
            )
        if self.declaration_source != self.DECLARATION_SOURCE:
            raise ValueError(
                "SBIR room-geometry declaration_source must be exactly "
                "USER_MEASUREMENT."
            )
        if not isinstance(self.room_description, RoomDescription):
            raise TypeError("SBIR room-geometry input requires RoomDescription.")
        if self.user_note is not None:
            if not isinstance(self.user_note, str):
                raise TypeError("SBIR room-geometry user_note must be text or null.")
            if not self.user_note or self.user_note != self.user_note.strip():
                raise ValueError(
                    "SBIR room-geometry user_note must be null or exact non-empty "
                    "text."
                )
