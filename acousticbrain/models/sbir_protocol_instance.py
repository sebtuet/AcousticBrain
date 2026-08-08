from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .evidence_acquisition import EvidenceAcquisitionPlan
from .experiment_discovery import ExperimentDescriptor
from .geometry_sbir_candidate import GeometrySBIRCandidate
from .loudspeaker_positioning_experiment import (
    LoudspeakerPositioningExperimentProposal,
)


class SBIRProtocolInstanceResolutionDecision(Enum):
    INPUT_SCHEMA_VALID = "INPUT_SCHEMA_VALID"
    PLAN_EXACTLY_RESOLVED = "PLAN_EXACTLY_RESOLVED"
    PLAN_FINGERPRINT_MATCHES = "PLAN_FINGERPRINT_MATCHES"
    PROTOCOL_EXACTLY_RESOLVED = "PROTOCOL_EXACTLY_RESOLVED"
    EXPERIMENTS_EXACTLY_RESOLVED = "EXPERIMENTS_EXACTLY_RESOLVED"
    GEOMETRY_CANDIDATE_EXACTLY_RESOLVED = (
        "GEOMETRY_CANDIDATE_EXACTLY_RESOLVED"
    )


class SBIRProtocolInstanceCompatibilityDecision(Enum):
    SPEAKER_SURFACE_MATCH = "SPEAKER_SURFACE_MATCH"
    DISPLACEMENT_SOURCE_MATCH = "DISPLACEMENT_SOURCE_MATCH"
    PROTOCOL_INSTANCE_COMPATIBLE = "PROTOCOL_INSTANCE_COMPATIBLE"


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


@dataclass(frozen=True)
class SBIRProtocolInstanceResolution:
    protocol_instance_input: SBIRProtocolInstanceInput
    source_plan: EvidenceAcquisitionPlan
    protocol_id: str
    reference_experiment: ExperimentDescriptor
    moved_experiment: ExperimentDescriptor
    geometry_candidate: GeometrySBIRCandidate
    decisions: tuple[SBIRProtocolInstanceResolutionDecision, ...]

    EXPECTED_DECISIONS = tuple(SBIRProtocolInstanceResolutionDecision)

    def __post_init__(self):
        value = self.protocol_instance_input
        if not isinstance(value, SBIRProtocolInstanceInput):
            raise TypeError("SBIR protocol-instance resolution requires its input.")
        if not isinstance(self.source_plan, EvidenceAcquisitionPlan):
            raise TypeError("SBIR protocol-instance resolution requires its plan.")
        if not isinstance(self.reference_experiment, ExperimentDescriptor):
            raise TypeError(
                "SBIR protocol-instance resolution requires its reference experiment."
            )
        if not isinstance(self.moved_experiment, ExperimentDescriptor):
            raise TypeError(
                "SBIR protocol-instance resolution requires its moved experiment."
            )
        if not isinstance(self.geometry_candidate, GeometrySBIRCandidate):
            raise TypeError(
                "SBIR protocol-instance resolution requires its geometry candidate."
            )
        if self.source_plan.plan_id != value.source_plan_id:
            raise ValueError("SBIR protocol-instance plan identity is inconsistent.")
        if self.protocol_id != value.protocol_id:
            raise ValueError("SBIR protocol-instance protocol identity is inconsistent.")
        if (
            self.reference_experiment.experiment_id
            != value.reference_experiment_id
        ):
            raise ValueError(
                "SBIR protocol-instance reference experiment identity is inconsistent."
            )
        if self.moved_experiment.experiment_id != value.moved_experiment_id:
            raise ValueError(
                "SBIR protocol-instance moved experiment identity is inconsistent."
            )
        if self.geometry_candidate.candidate_id != value.geometry_candidate_id:
            raise ValueError(
                "SBIR protocol-instance geometry candidate identity is inconsistent."
            )
        if self.decisions != self.EXPECTED_DECISIONS:
            raise ValueError(
                "SBIR protocol-instance resolution decisions are incomplete or "
                "out of order."
            )


@dataclass(frozen=True)
class SBIRProtocolInstanceCompatibility:
    resolution: SBIRProtocolInstanceResolution
    displacement_proposal: LoudspeakerPositioningExperimentProposal
    decisions: tuple[SBIRProtocolInstanceCompatibilityDecision, ...]

    EXPECTED_DECISIONS = tuple(SBIRProtocolInstanceCompatibilityDecision)

    def __post_init__(self):
        if not isinstance(self.resolution, SBIRProtocolInstanceResolution):
            raise TypeError("SBIR protocol-instance compatibility requires resolution.")
        if not isinstance(
            self.displacement_proposal,
            LoudspeakerPositioningExperimentProposal,
        ):
            raise TypeError(
                "SBIR protocol-instance compatibility requires a displacement "
                "proposal."
            )
        value = self.resolution.protocol_instance_input
        candidate = self.resolution.geometry_candidate
        proposal = self.displacement_proposal
        if candidate.speaker_id != value.speaker_id:
            raise ValueError(
                "SBIR protocol-instance compatible speaker identity is inconsistent."
            )
        if candidate.surface_id != value.surface_id:
            raise ValueError(
                "SBIR protocol-instance compatible surface identity is inconsistent."
            )
        if proposal.source_geometry_candidate_id != candidate.candidate_id:
            raise ValueError(
                "SBIR protocol-instance displacement proposal association is "
                "inconsistent."
            )
        if proposal.source_surface_id != candidate.surface_id:
            raise ValueError(
                "SBIR protocol-instance displacement proposal surface is inconsistent."
            )
        if proposal.step_distance_m != value.speaker_displacement_m:
            raise ValueError(
                "SBIR protocol-instance displacement proposal value is inconsistent."
            )
        if self.decisions != self.EXPECTED_DECISIONS:
            raise ValueError(
                "SBIR protocol-instance compatibility decisions are incomplete or "
                "out of order."
            )


@dataclass(frozen=True)
class SBIRProtocolInstanceRecord:
    protocol_instance_input: SBIRProtocolInstanceInput
    source_plan_id: str
    source_plan_contract_fingerprint: str
    protocol_id: str
    reference_experiment_id: str
    moved_experiment_id: str
    geometry_candidate_id: str
    displacement_proposal_id: str
    resolution_decisions: tuple[SBIRProtocolInstanceResolutionDecision, ...]
    compatibility_decisions: tuple[
        SBIRProtocolInstanceCompatibilityDecision,
        ...,
    ]

    def __post_init__(self):
        value = self.protocol_instance_input
        if not isinstance(value, SBIRProtocolInstanceInput):
            raise TypeError("SBIR protocol-instance record requires its input.")
        expected = (
            ("source_plan_id", self.source_plan_id, value.source_plan_id),
            (
                "source_plan_contract_fingerprint",
                self.source_plan_contract_fingerprint,
                value.source_plan_contract_fingerprint,
            ),
            ("protocol_id", self.protocol_id, value.protocol_id),
            (
                "reference_experiment_id",
                self.reference_experiment_id,
                value.reference_experiment_id,
            ),
            (
                "moved_experiment_id",
                self.moved_experiment_id,
                value.moved_experiment_id,
            ),
            (
                "geometry_candidate_id",
                self.geometry_candidate_id,
                value.geometry_candidate_id,
            ),
        )
        inconsistent = tuple(
            field for field, actual, declared in expected if actual != declared
        )
        if inconsistent:
            raise ValueError(
                "SBIR protocol-instance record provenance is inconsistent: "
                + ", ".join(inconsistent)
                + "."
            )
        if (
            not isinstance(self.displacement_proposal_id, str)
            or not self.displacement_proposal_id
            or self.displacement_proposal_id
            != self.displacement_proposal_id.strip()
        ):
            raise ValueError(
                "SBIR protocol-instance displacement proposal id must be exact."
            )
        if self.resolution_decisions != (
            SBIRProtocolInstanceResolution.EXPECTED_DECISIONS
        ):
            raise ValueError(
                "SBIR protocol-instance record resolution decisions are invalid."
            )
        if self.compatibility_decisions != (
            SBIRProtocolInstanceCompatibility.EXPECTED_DECISIONS
        ):
            raise ValueError(
                "SBIR protocol-instance record compatibility decisions are invalid."
            )

    @classmethod
    def from_compatibility(cls, compatibility):
        if not isinstance(compatibility, SBIRProtocolInstanceCompatibility):
            raise TypeError("SBIR protocol-instance compatibility is required.")
        resolution = compatibility.resolution
        value = resolution.protocol_instance_input
        return cls(
            protocol_instance_input=value,
            source_plan_id=resolution.source_plan.plan_id,
            source_plan_contract_fingerprint=(
                value.source_plan_contract_fingerprint
            ),
            protocol_id=resolution.protocol_id,
            reference_experiment_id=resolution.reference_experiment.experiment_id,
            moved_experiment_id=resolution.moved_experiment.experiment_id,
            geometry_candidate_id=resolution.geometry_candidate.candidate_id,
            displacement_proposal_id=(
                compatibility.displacement_proposal.proposal_id
            ),
            resolution_decisions=resolution.decisions,
            compatibility_decisions=compatibility.decisions,
        )


@dataclass(frozen=True)
class SBIRProtocolInstanceRegistry:
    records: tuple[SBIRProtocolInstanceRecord, ...] = ()

    def __post_init__(self):
        if not isinstance(self.records, tuple) or any(
            not isinstance(value, SBIRProtocolInstanceRecord)
            for value in self.records
        ):
            raise TypeError(
                "SBIR protocol-instance registry requires typed records."
            )
        identifiers = tuple(
            value.protocol_instance_input.protocol_instance_id
            for value in self.records
        )
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("SBIR protocol-instance ids must be unique.")

    def with_record(self, record):
        if not isinstance(record, SBIRProtocolInstanceRecord):
            raise TypeError("SBIR protocol-instance record is required.")
        identifier = record.protocol_instance_input.protocol_instance_id
        existing = tuple(
            value
            for value in self.records
            if value.protocol_instance_input.protocol_instance_id == identifier
        )
        if existing:
            if existing[0] == record:
                return self
            fields = tuple(sorted(_sbir_different_fields(existing[0], record)))
            raise ValueError(
                "SBIR_PROTOCOL_INSTANCE_DIVERGENT: incompatible fields: "
                + ", ".join(fields)
            )
        return SBIRProtocolInstanceRegistry(tuple(sorted(
            (*self.records, record),
            key=lambda value: value.protocol_instance_input.protocol_instance_id,
        )))


def _sbir_different_fields(left, right, prefix=""):
    from dataclasses import fields, is_dataclass

    if type(left) is not type(right):
        return (prefix or "record",)
    if is_dataclass(left):
        result = ()
        for field in fields(left):
            name = f"{prefix}.{field.name}" if prefix else field.name
            result += _sbir_different_fields(
                getattr(left, field.name),
                getattr(right, field.name),
                name,
            )
        return result
    return () if left == right else (prefix,)
