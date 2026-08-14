from dataclasses import dataclass
from enum import Enum, IntEnum
from math import isfinite


class GuidedQuestionKind(Enum):
    GEOMETRY = "GEOMETRY"
    SURFACE = "SURFACE"
    MATERIAL_ASSIGNMENT = "MATERIAL_ASSIGNMENT"
    PLACEMENT = "PLACEMENT"


class GuidedQuestionPriority(IntEnum):
    LOW = 25
    MEDIUM = 50
    HIGH = 75
    CRITICAL = 100


@dataclass(frozen=True)
class GuidedAllowedValue:
    value_id: str
    display_name: str
    catalog_entry_id: str | None = None

    def __post_init__(self):
        for value, label in (
            (self.value_id, "value"),
            (self.display_name, "display name"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Guided-question {label} is required.")
        if self.catalog_entry_id is not None and (
            not isinstance(self.catalog_entry_id, str)
            or not self.catalog_entry_id.strip()
        ):
            raise ValueError("Guided-question catalog identifier cannot be empty.")


@dataclass(frozen=True)
class RoomDescriptionQuestionPlan:
    question_id: str
    question_kind: GuidedQuestionKind
    fact_code: str
    priority: GuidedQuestionPriority
    target_kind: str | None
    target_id: str | None
    target_role: str | None
    target_candidates: tuple[str, ...]
    allowed_values: tuple[GuidedAllowedValue, ...]
    validation_constraints: tuple[str, ...]
    unknown_consequences: tuple[str, ...]
    requires_target_confirmation: bool = False

    def __post_init__(self):
        for value, label in (
            (self.question_id, "identifier"),
            (self.fact_code, "fact code"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Question-plan {label} is required.")
        if not isinstance(self.question_kind, GuidedQuestionKind):
            raise ValueError("Question plan requires a typed kind.")
        if not isinstance(self.priority, GuidedQuestionPriority):
            raise ValueError("Question plan requires a typed priority.")
        if self.target_kind not in {None, "SURFACE", "REGION"}:
            raise ValueError("Question plan has an invalid target kind.")
        for collection in (
            self.target_candidates,
            self.validation_constraints,
            self.unknown_consequences,
        ):
            if not isinstance(collection, tuple) or any(
                not isinstance(item, str) or not item.strip() for item in collection
            ):
                raise ValueError("Question-plan codes must be non-empty tuples.")
        if not isinstance(self.allowed_values, tuple) or any(
            not isinstance(item, GuidedAllowedValue) for item in self.allowed_values
        ):
            raise ValueError("Question-plan allowed values must be typed.")
        if len(self.target_candidates) != len(set(self.target_candidates)):
            raise ValueError("Question-plan target candidates must be unique.")
        value_ids = tuple(item.value_id for item in self.allowed_values)
        if len(value_ids) != len(set(value_ids)):
            raise ValueError("Question-plan allowed values must be unique.")
        if self.requires_target_confirmation and len(self.target_candidates) < 2:
            raise ValueError("Target confirmation requires multiple candidates.")
        if self.target_id is not None and self.target_id not in self.target_candidates:
            raise ValueError("Question-plan target must be an allowed candidate.")


class GuidedInterpretationStatus(Enum):
    CANDIDATE = "CANDIDATE"
    AMBIGUOUS = "AMBIGUOUS"
    CONTRADICTORY = "CONTRADICTORY"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass(frozen=True)
class GuidedAnswerInterpretation:
    status: GuidedInterpretationStatus
    candidate_value_ids: tuple[str, ...] = ()
    target_id: str | None = None
    confidence: float = 0.0
    ambiguity_codes: tuple[str, ...] = ()
    provenance_codes: tuple[str, ...] = ("USER_DESCRIPTION_INTERPRETED",)

    def __post_init__(self):
        if not isinstance(self.status, GuidedInterpretationStatus):
            raise ValueError("Guided interpretation requires a typed status.")
        for collection in (
            self.candidate_value_ids,
            self.ambiguity_codes,
            self.provenance_codes,
        ):
            if not isinstance(collection, tuple) or any(
                not isinstance(item, str) or not item.strip() for item in collection
            ):
                raise ValueError("Guided interpretation codes must be tuples.")
        if (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, (int, float))
            or not isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 100.0
        ):
            raise ValueError("Guided interpretation confidence must be bounded.")


class GuidedChangeKind(Enum):
    ASSIGN_CATALOG_MATERIAL = "ASSIGN_CATALOG_MATERIAL"


@dataclass(frozen=True)
class GuidedRequestedChange:
    change_kind: GuidedChangeKind
    target_kind: str
    target_id: str
    value_id: str
    catalog_entry_id: str | None = None

    def __post_init__(self):
        if not isinstance(self.change_kind, GuidedChangeKind):
            raise ValueError("Requested change requires a typed kind.")
        if self.target_kind not in {"SURFACE", "REGION"}:
            raise ValueError("Requested change has an invalid target kind.")
        for value in (self.target_id, self.value_id):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Requested-change identifiers are required.")


@dataclass(frozen=True)
class GuidedInterpretedFact:
    fact_code: str
    value: str
    confidence: float
    provenance_codes: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.fact_code, str) or not self.fact_code.strip():
            raise ValueError("Interpreted fact requires a code.")
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Interpreted fact requires a value.")
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Interpreted-fact confidence must be bounded.")


@dataclass(frozen=True)
class GuidedValidationIssue:
    code: str
    field: str
    related_ids: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.code or not self.field:
            raise ValueError("Proposal validation issue requires code and field.")


@dataclass(frozen=True)
class GuidedCompletenessProjection:
    before: float
    after: float

    def __post_init__(self):
        if any(not isfinite(value) or not 0.0 <= value <= 100.0 for value in (self.before, self.after)):
            raise ValueError("Completeness projection must be bounded.")

    @property
    def change(self):
        return self.after - self.before


class RoomDescriptionChangeProposalStatus(Enum):
    DRAFT = "DRAFT"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    INVALID = "INVALID"
    READY_FOR_CONFIRMATION = "READY_FOR_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class RoomDescriptionChangeProposal:
    proposal_id: str
    target_kind: str | None
    target_id: str | None
    requested_changes: tuple[GuidedRequestedChange, ...]
    interpreted_facts: tuple[GuidedInterpretedFact, ...]
    unresolved_ambiguities: tuple[str, ...]
    validation_issues: tuple[GuidedValidationIssue, ...]
    predicted_completeness_change: GuidedCompletenessProjection
    potentially_unblocked_capabilities: tuple[str, ...]
    requires_confirmation: bool
    status: RoomDescriptionChangeProposalStatus
    provenance: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.proposal_id, str) or not self.proposal_id.strip():
            raise ValueError("Change proposal requires an identifier.")
        typed = (
            (self.requested_changes, GuidedRequestedChange),
            (self.interpreted_facts, GuidedInterpretedFact),
            (self.validation_issues, GuidedValidationIssue),
        )
        for collection, expected in typed:
            if not isinstance(collection, tuple) or any(
                not isinstance(item, expected) for item in collection
            ):
                raise ValueError("Change proposal contains invalid typed data.")
        for collection in (
            self.unresolved_ambiguities,
            self.potentially_unblocked_capabilities,
            self.provenance,
        ):
            if not isinstance(collection, tuple):
                raise ValueError("Change-proposal code collections must be tuples.")
        if not isinstance(self.status, RoomDescriptionChangeProposalStatus):
            raise ValueError("Change proposal requires a typed status.")
        if self.status is RoomDescriptionChangeProposalStatus.READY_FOR_CONFIRMATION and not self.requires_confirmation:
            raise ValueError("Ready proposals require explicit confirmation.")
        if self.status is RoomDescriptionChangeProposalStatus.APPLIED and self.requires_confirmation:
            raise ValueError("Applied proposals cannot still require confirmation.")
