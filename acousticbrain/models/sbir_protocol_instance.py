from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class SBIRProtocolInstanceInput:
    schema_version: int
    protocol_instance_id: str
    protocol_id: str
    source_plan_id: str
    source_plan_contract_fingerprint: str
    reference_experiment_id: str
    moved_experiment_id: str
    speaker_id: str
    surface_id: str
    geometry_candidate_id: str
    speaker_displacement_m: int | float
    declaration_source: str
    user_note: str | None

    CURRENT_SCHEMA_VERSION = 1
    PROTOCOL_ID = "protocol.temporary_move_speaker.v1"
    SOURCE_PLAN_ID = (
        "EVIDENCE_ACQUISITION_SBIR_PLACEMENT_INTERACTION_REASONING_"
        "ACQUIRE_SUPPORTING_OBSERVATION_V2"
    )
    DECLARATION_SOURCE = "STRUCTURED_SCIENTIFIC_SOURCE"

    def __post_init__(self):
        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
            or self.schema_version != self.CURRENT_SCHEMA_VERSION
        ):
            raise ValueError("Unsupported SBIR protocol-instance schema version.")

        exact_text_fields = (
            ("protocol_instance_id", self.protocol_instance_id),
            ("protocol_id", self.protocol_id),
            ("source_plan_id", self.source_plan_id),
            ("reference_experiment_id", self.reference_experiment_id),
            ("moved_experiment_id", self.moved_experiment_id),
            ("speaker_id", self.speaker_id),
            ("surface_id", self.surface_id),
            ("geometry_candidate_id", self.geometry_candidate_id),
            ("declaration_source", self.declaration_source),
        )
        for field, value in exact_text_fields:
            if not isinstance(value, str):
                raise TypeError(
                    f"SBIR protocol-instance field {field} must be a string."
                )
            if not value or value != value.strip():
                raise ValueError(
                    f"SBIR protocol-instance field {field} must be an exact "
                    "non-empty string."
                )

        if self.protocol_id != self.PROTOCOL_ID:
            raise ValueError(
                "SBIR protocol-instance protocol_id must be exactly "
                f"{self.PROTOCOL_ID}."
            )
        if self.source_plan_id != self.SOURCE_PLAN_ID:
            raise ValueError(
                "SBIR protocol-instance source_plan_id must be exactly "
                f"{self.SOURCE_PLAN_ID}."
            )
        if self.declaration_source != self.DECLARATION_SOURCE:
            raise ValueError(
                "SBIR protocol-instance declaration_source must be exactly "
                f"{self.DECLARATION_SOURCE}."
            )

        fingerprint = self.source_plan_contract_fingerprint
        if (
            not isinstance(fingerprint, str)
            or len(fingerprint) != 64
            or any(character not in "0123456789abcdef" for character in fingerprint)
        ):
            raise ValueError(
                "SBIR protocol-instance source plan fingerprint must be canonical "
                "SHA-256."
            )

        if self.reference_experiment_id == self.moved_experiment_id:
            raise ValueError(
                "SBIR protocol-instance reference and moved experiments must differ."
            )

        displacement = self.speaker_displacement_m
        if (
            not isinstance(displacement, (int, float))
            or isinstance(displacement, bool)
            or displacement == 0
            or (isinstance(displacement, float) and not isfinite(displacement))
        ):
            raise ValueError(
                "SBIR protocol-instance speaker_displacement_m must be a finite, "
                "non-zero JSON number."
            )

        if self.user_note is not None:
            if not isinstance(self.user_note, str):
                raise TypeError(
                    "SBIR protocol-instance user_note must be text or null."
                )
            if not self.user_note or self.user_note != self.user_note.strip():
                raise ValueError(
                    "SBIR protocol-instance user_note must be null or exact "
                    "non-empty text."
                )
