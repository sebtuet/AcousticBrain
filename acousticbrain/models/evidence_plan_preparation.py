from dataclasses import dataclass
from enum import Enum

from .evidence_acquisition import EvidenceAcquisitionPlan


class EvidencePlanPrerequisiteStatus(Enum):
    CONFIRMED = "CONFIRMED"
    NOT_CONFIRMED = "NOT_CONFIRMED"
    UNKNOWN = "UNKNOWN"


class EvidencePlanPreparationResolutionStatus(Enum):
    PLAN_EXACTLY_RESOLVED = "PLAN_EXACTLY_RESOLVED"


class EvidencePlanPreparationDeclarationStatus(Enum):
    PREPARATION_DECLARED = "PREPARATION_DECLARED"


class EvidencePlanAllPrerequisitesStatus(Enum):
    ALL_PREREQUISITES_USER_CONFIRMED = "ALL_PREREQUISITES_USER_CONFIRMED"


@dataclass(frozen=True)
class EvidencePlanPrerequisiteDeclaration:
    code: str
    status: EvidencePlanPrerequisiteStatus

    def __post_init__(self):
        if (
            not isinstance(self.code, str)
            or not self.code
            or self.code != self.code.strip()
        ):
            raise ValueError(
                "Evidence-plan prerequisite code must be an exact non-empty string."
            )
        if not isinstance(self.status, EvidencePlanPrerequisiteStatus):
            raise ValueError("Evidence-plan prerequisite status is invalid.")


@dataclass(frozen=True)
class EvidencePlanPreparationConfirmationInput:
    schema_version: int
    confirmation_id: str
    plan_id: str
    plan_contract_fingerprint: str
    prerequisites: tuple[EvidencePlanPrerequisiteDeclaration, ...]
    declaration_source: str
    user_note: str | None = None

    CURRENT_SCHEMA_VERSION = 1

    def __post_init__(self):
        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
            or self.schema_version != self.CURRENT_SCHEMA_VERSION
        ):
            raise ValueError(
                "Unsupported evidence-plan preparation schema version."
            )
        for field, value in (
            ("confirmation_id", self.confirmation_id),
            ("plan_id", self.plan_id),
            ("declaration_source", self.declaration_source),
        ):
            if not isinstance(value, str):
                raise TypeError(
                    f"Evidence-plan preparation field {field} must be a string."
                )
            if not value or value != value.strip():
                raise ValueError(
                    f"Evidence-plan preparation field {field} must be an exact "
                    "non-empty string."
                )
        fingerprint = self.plan_contract_fingerprint
        if (
            not isinstance(fingerprint, str)
            or len(fingerprint) != 64
            or any(value not in "0123456789abcdef" for value in fingerprint)
        ):
            raise ValueError(
                "Evidence-plan preparation fingerprint must be canonical SHA-256."
            )
        if not isinstance(self.prerequisites, tuple) or any(
            not isinstance(value, EvidencePlanPrerequisiteDeclaration)
            for value in self.prerequisites
        ):
            raise TypeError(
                "Evidence-plan preparation prerequisites must be typed and immutable."
            )
        codes = tuple(value.code for value in self.prerequisites)
        if len(codes) != len(set(codes)):
            raise ValueError(
                "Evidence-plan preparation prerequisite codes must be unique."
            )
        object.__setattr__(
            self,
            "prerequisites",
            tuple(sorted(self.prerequisites, key=lambda value: value.code)),
        )
        if self.user_note is not None:
            if not isinstance(self.user_note, str):
                raise TypeError(
                    "Evidence-plan preparation user note must be text or absent."
                )
            if not self.user_note or self.user_note != self.user_note.strip():
                raise ValueError(
                    "Evidence-plan preparation user note must be absent or exact "
                    "non-empty text."
                )


@dataclass(frozen=True)
class EvidencePlanPreparationResolution:
    confirmation_input: EvidencePlanPreparationConfirmationInput
    plan: EvidenceAcquisitionPlan
    status: EvidencePlanPreparationResolutionStatus

    def __post_init__(self):
        if not isinstance(
            self.confirmation_input,
            EvidencePlanPreparationConfirmationInput,
        ):
            raise TypeError("Evidence-plan preparation input is required.")
        if not isinstance(self.plan, EvidenceAcquisitionPlan):
            raise TypeError("Evidence-plan preparation plan is required.")
        if self.plan.plan_id != self.confirmation_input.plan_id:
            raise ValueError("Evidence-plan preparation plan identity is inconsistent.")
        if self.status is not (
            EvidencePlanPreparationResolutionStatus.PLAN_EXACTLY_RESOLVED
        ):
            raise ValueError("Evidence-plan preparation resolution status is invalid.")


@dataclass(frozen=True)
class EvidencePlanPreparationDeclaration:
    resolution: EvidencePlanPreparationResolution
    declaration_status: EvidencePlanPreparationDeclarationStatus
    all_prerequisites_status: EvidencePlanAllPrerequisitesStatus | None

    def __post_init__(self):
        if not isinstance(self.resolution, EvidencePlanPreparationResolution):
            raise TypeError("Evidence-plan preparation resolution is required.")
        if self.declaration_status is not (
            EvidencePlanPreparationDeclarationStatus.PREPARATION_DECLARED
        ):
            raise ValueError("Evidence-plan preparation declaration status is invalid.")
        all_confirmed = all(
            value.status is EvidencePlanPrerequisiteStatus.CONFIRMED
            for value in self.resolution.confirmation_input.prerequisites
        )
        expected = (
            EvidencePlanAllPrerequisitesStatus.ALL_PREREQUISITES_USER_CONFIRMED
            if all_confirmed
            else None
        )
        if self.all_prerequisites_status is not expected:
            raise ValueError(
                "Evidence-plan preparation all-prerequisites decision is invalid."
            )


@dataclass(frozen=True)
class EvidencePlanPreparationRecord:
    confirmation_input: EvidencePlanPreparationConfirmationInput
    resolution_status: EvidencePlanPreparationResolutionStatus
    declaration_status: EvidencePlanPreparationDeclarationStatus
    all_prerequisites_status: EvidencePlanAllPrerequisitesStatus | None

    def __post_init__(self):
        if not isinstance(
            self.confirmation_input, EvidencePlanPreparationConfirmationInput
        ):
            raise TypeError("Evidence-plan preparation record requires its input.")
        if self.resolution_status is not (
            EvidencePlanPreparationResolutionStatus.PLAN_EXACTLY_RESOLVED
        ):
            raise ValueError("Evidence-plan preparation record resolution is invalid.")
        if self.declaration_status is not (
            EvidencePlanPreparationDeclarationStatus.PREPARATION_DECLARED
        ):
            raise ValueError("Evidence-plan preparation record declaration is invalid.")
        all_confirmed = all(
            value.status is EvidencePlanPrerequisiteStatus.CONFIRMED
            for value in self.confirmation_input.prerequisites
        )
        expected = (
            EvidencePlanAllPrerequisitesStatus.ALL_PREREQUISITES_USER_CONFIRMED
            if all_confirmed
            else None
        )
        if self.all_prerequisites_status is not expected:
            raise ValueError(
                "Evidence-plan preparation record all-prerequisites decision is invalid."
            )

    @classmethod
    def from_declaration(cls, declaration):
        if not isinstance(declaration, EvidencePlanPreparationDeclaration):
            raise TypeError("Evidence-plan preparation declaration is required.")
        return cls(
            confirmation_input=declaration.resolution.confirmation_input,
            resolution_status=declaration.resolution.status,
            declaration_status=declaration.declaration_status,
            all_prerequisites_status=declaration.all_prerequisites_status,
        )


@dataclass(frozen=True)
class EvidencePlanPreparationRegistry:
    records: tuple[EvidencePlanPreparationRecord, ...] = ()

    def __post_init__(self):
        if not isinstance(self.records, tuple) or any(
            not isinstance(value, EvidencePlanPreparationRecord)
            for value in self.records
        ):
            raise TypeError("Evidence-plan preparation registry requires typed records.")
        identifiers = tuple(
            value.confirmation_input.confirmation_id for value in self.records
        )
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Evidence-plan preparation confirmation ids must be unique.")

    def with_record(self, record):
        if not isinstance(record, EvidencePlanPreparationRecord):
            raise TypeError("Evidence-plan preparation record is required.")
        identifier = record.confirmation_input.confirmation_id
        existing = tuple(
            value for value in self.records
            if value.confirmation_input.confirmation_id == identifier
        )
        if existing:
            if existing[0] == record:
                return self
            fields = tuple(sorted(_different_preparation_fields(existing[0], record)))
            raise ValueError(
                "PREPARATION_CONFIRMATION_DIVERGENT: incompatible fields: "
                + ", ".join(fields)
            )
        return EvidencePlanPreparationRegistry(tuple(sorted(
            (*self.records, record),
            key=lambda value: value.confirmation_input.confirmation_id,
        )))


def _different_preparation_fields(left, right, prefix=""):
    from dataclasses import fields, is_dataclass

    if type(left) is not type(right):
        return (prefix or "record",)
    if is_dataclass(left):
        result = ()
        for field in fields(left):
            name = f"{prefix}.{field.name}" if prefix else field.name
            result += _different_preparation_fields(
                getattr(left, field.name), getattr(right, field.name), name
            )
        return result
    return () if left == right else (prefix,)
