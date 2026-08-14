from dataclasses import dataclass
from enum import Enum


class ReflectionExperimentDeclarationStatus(Enum):
    PLANNED = "PLANNED"
    EXECUTED = "EXECUTED"
    INVALID = "INVALID"
    CANCELLED = "CANCELLED"


class ReflectionDeclarationProvenanceSource(Enum):
    SYSTEM_DERIVED = "SYSTEM_DERIVED"
    UPSTREAM_ANALYSIS = "UPSTREAM_ANALYSIS"
    USER_DECLARATION = "USER_DECLARATION"
    MEASUREMENT_MANIFEST = "MEASUREMENT_MANIFEST"


@dataclass(frozen=True)
class ReflectionDeclarationFieldProvenance:
    field_code: str
    source: ReflectionDeclarationProvenanceSource
    source_id: str
    provenance_codes: tuple[str, ...]

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.field_code, self.source_id)
        ):
            raise ValueError("Declaration field provenance identifiers are required.")
        if not isinstance(self.source, ReflectionDeclarationProvenanceSource):
            raise ValueError("Declaration field provenance source is invalid.")
        if (
            not isinstance(self.provenance_codes, tuple)
            or not self.provenance_codes
            or any(
                not isinstance(item, str) or not item.strip()
                for item in self.provenance_codes
            )
        ):
            raise ValueError("Declaration field provenance codes are required.")


def _validate_field_provenance(values, required_fields):
    if not isinstance(values, tuple) or any(
        not isinstance(item, ReflectionDeclarationFieldProvenance)
        for item in values
    ):
        raise ValueError("Declaration field provenance must be a typed tuple.")
    fields = tuple(item.field_code for item in values)
    if len(fields) != len(set(fields)):
        raise ValueError("Declaration field provenance must be unique.")
    if set(fields) != set(required_fields):
        raise ValueError("Declaration field provenance coverage is incomplete.")


@dataclass(frozen=True)
class ReflectionExperimentMeasurementReference:
    reference_id: str
    experiment_id: str
    measurement_name: str
    content_hash: str | None
    field_provenance: tuple[ReflectionDeclarationFieldProvenance, ...]

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.reference_id, self.experiment_id, self.measurement_name)
        ):
            raise ValueError("Reflection measurement references require identifiers.")
        if self.content_hash is not None and (
            not isinstance(self.content_hash, str) or not self.content_hash.strip()
        ):
            raise ValueError("Reflection measurement content hashes cannot be empty.")
        required = ["reference_id", "experiment_id", "measurement_name"]
        if self.content_hash is not None:
            required.append("content_hash")
        _validate_field_provenance(self.field_provenance, tuple(required))


@dataclass(frozen=True)
class ReflectionExperimentConditionDeclaration:
    condition_code: str
    measurement_references: tuple[ReflectionExperimentMeasurementReference, ...]
    field_provenance: tuple[ReflectionDeclarationFieldProvenance, ...]

    def __post_init__(self):
        if not isinstance(self.condition_code, str) or not self.condition_code.strip():
            raise ValueError("Reflection experiment condition code is required.")
        if not isinstance(self.measurement_references, tuple) or any(
            not isinstance(item, ReflectionExperimentMeasurementReference)
            for item in self.measurement_references
        ):
            raise ValueError("Reflection condition measurements must be a typed tuple.")
        reference_ids = tuple(item.reference_id for item in self.measurement_references)
        if len(reference_ids) != len(set(reference_ids)):
            raise ValueError("Reflection condition measurement references must be unique.")
        _validate_field_provenance(
            self.field_provenance,
            ("condition_code", "measurement_references"),
        )


@dataclass(frozen=True)
class ControlledReflectionExperimentDeclaration:
    declaration_id: str
    proposal_id: str
    status: ReflectionExperimentDeclarationStatus
    reference_condition: ReflectionExperimentConditionDeclaration
    intervention_condition: ReflectionExperimentConditionDeclaration
    status_reason_code: str | None
    field_provenance: tuple[ReflectionDeclarationFieldProvenance, ...]

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.declaration_id, self.proposal_id)
        ):
            raise ValueError("Reflection experiment declaration identifiers are required.")
        if self.declaration_id != f"reflection_experiment_declaration.{self.proposal_id}":
            raise ValueError("Reflection declaration identifier must derive from proposal id.")
        if not isinstance(self.status, ReflectionExperimentDeclarationStatus):
            raise ValueError("Reflection experiment declaration status is invalid.")
        if not isinstance(
            self.reference_condition, ReflectionExperimentConditionDeclaration
        ) or not isinstance(
            self.intervention_condition, ReflectionExperimentConditionDeclaration
        ):
            raise ValueError("Reflection experiment conditions are required.")
        if self.reference_condition.condition_code == (
            self.intervention_condition.condition_code
        ):
            raise ValueError("Reference and intervention conditions must differ.")
        reference_ids = {
            item.reference_id
            for item in self.reference_condition.measurement_references
        }
        intervention_ids = {
            item.reference_id
            for item in self.intervention_condition.measurement_references
        }
        if reference_ids & intervention_ids:
            raise ValueError("A measurement cannot belong to both conditions.")
        if self.status is ReflectionExperimentDeclarationStatus.EXECUTED and (
            not reference_ids or not intervention_ids
        ):
            raise ValueError("Executed declarations require both measurement conditions.")
        requires_reason = self.status in {
            ReflectionExperimentDeclarationStatus.INVALID,
            ReflectionExperimentDeclarationStatus.CANCELLED,
        }
        if requires_reason != (self.status_reason_code is not None):
            raise ValueError("Declaration status reason is inconsistent with status.")
        if self.status_reason_code is not None and (
            not isinstance(self.status_reason_code, str)
            or not self.status_reason_code.strip()
        ):
            raise ValueError("Declaration status reason cannot be empty.")
        required = [
            "declaration_id",
            "proposal_id",
            "status",
            "reference_condition",
            "intervention_condition",
        ]
        if self.status_reason_code is not None:
            required.append("status_reason_code")
        _validate_field_provenance(self.field_provenance, tuple(required))


@dataclass(frozen=True)
class ControlledReflectionExperimentDeclarationRegistry:
    declarations: tuple[ControlledReflectionExperimentDeclaration, ...]
    schema_version: int = 1

    def __post_init__(self):
        if self.schema_version != 1:
            raise ValueError("Unsupported reflection declaration schema version.")
        if not isinstance(self.declarations, tuple) or any(
            not isinstance(item, ControlledReflectionExperimentDeclaration)
            for item in self.declarations
        ):
            raise ValueError("Reflection declaration registry must be a typed tuple.")
        identifiers = tuple(item.declaration_id for item in self.declarations)
        proposals = tuple(item.proposal_id for item in self.declarations)
        if len(identifiers) != len(set(identifiers)) or len(proposals) != len(
            set(proposals)
        ):
            raise ValueError("Reflection declarations must be unique per proposal.")
