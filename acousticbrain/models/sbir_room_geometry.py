from dataclasses import dataclass
from enum import Enum

from .experiment_discovery import ExperimentDescriptor, ExperimentType
from .room_description import RoomDescription
from .room_geometry import RoomGeometry


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


class SBIRRoomGeometryResolutionDecision(Enum):
    ROOM_DESCRIPTION_SCHEMA_VALID = "ROOM_DESCRIPTION_SCHEMA_VALID"
    BASELINE_EXACTLY_RESOLVED = "BASELINE_EXACTLY_RESOLVED"
    SBIR_GEOMETRY_ENTITY_SET_EXACT = "SBIR_GEOMETRY_ENTITY_SET_EXACT"
    ROOM_GEOMETRY_RELATIONALLY_VALID = "ROOM_GEOMETRY_RELATIONALLY_VALID"
    GEOMETRY_QUALITY_SET_EXACT = "GEOMETRY_QUALITY_SET_EXACT"
    LEGACY_GEOMETRY_NON_CONFLICTING = "LEGACY_GEOMETRY_NON_CONFLICTING"
    SBIR_GEOMETRY_DECLARATION_READY = "SBIR_GEOMETRY_DECLARATION_READY"


@dataclass(frozen=True)
class SBIRRoomGeometryResolution:
    declaration_input: SBIRRoomGeometryDeclarationInput
    baseline_experiment: ExperimentDescriptor
    room_geometry: RoomGeometry
    decisions: tuple[SBIRRoomGeometryResolutionDecision, ...]

    EXPECTED_DECISIONS = tuple(SBIRRoomGeometryResolutionDecision)[:5]

    def __post_init__(self):
        if not isinstance(
            self.declaration_input, SBIRRoomGeometryDeclarationInput
        ):
            raise TypeError(
                "SBIR room-geometry resolution requires a declaration input."
            )
        if not isinstance(self.baseline_experiment, ExperimentDescriptor):
            raise TypeError(
                "SBIR room-geometry resolution requires an experiment descriptor."
            )
        if (
            self.baseline_experiment.experiment_id
            != self.declaration_input.target_experiment_id
            or self.baseline_experiment.experiment_type
            is not ExperimentType.BASELINE
        ):
            raise ValueError(
                "SBIR room-geometry resolution baseline is inconsistent."
            )
        if not isinstance(self.room_geometry, RoomGeometry):
            raise TypeError(
                "SBIR room-geometry resolution requires built room geometry."
            )
        if self.decisions != self.EXPECTED_DECISIONS:
            raise ValueError(
                "SBIR room-geometry resolution decisions must be exact and ordered."
            )


@dataclass(frozen=True)
class SBIRRoomGeometryPreview:
    resolution: SBIRRoomGeometryResolution
    legacy_geometry_present: bool
    decisions: tuple[SBIRRoomGeometryResolutionDecision, ...]

    EXPECTED_DECISIONS = tuple(SBIRRoomGeometryResolutionDecision)

    def __post_init__(self):
        if not isinstance(self.resolution, SBIRRoomGeometryResolution):
            raise TypeError(
                "SBIR room-geometry preview requires an exact resolution."
            )
        if not isinstance(self.legacy_geometry_present, bool):
            raise TypeError(
                "SBIR room-geometry legacy presence must be explicit."
            )
        if self.decisions != self.EXPECTED_DECISIONS:
            raise ValueError(
                "SBIR room-geometry preview decisions must be exact and ordered."
            )
