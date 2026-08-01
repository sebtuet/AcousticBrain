from dataclasses import dataclass
from enum import Enum

from .evidence_acquisition import EvidenceAcquisitionPlan
from .listening_position_sampling_protocol import (
    ListeningPositionSamplingProtocol,
)


class EvidencePlanCompletionReferenceKind(Enum):
    PROTOCOL = "PROTOCOL"
    PLAN = "PLAN"


class EvidencePlanCompletionResolutionStatus(Enum):
    REFERENCE_RESOLVED = "REFERENCE_RESOLVED"


@dataclass(frozen=True)
class EvidencePlanCompletionInput:
    schema_version: int
    completion_input_id: str
    source_plan_id: str
    reference_kind: EvidencePlanCompletionReferenceKind
    reference_id: str
    declaration_source: str
    user_note: str | None = None

    CURRENT_SCHEMA_VERSION = 1

    def __post_init__(self):
        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
            or self.schema_version != self.CURRENT_SCHEMA_VERSION
        ):
            raise ValueError("Unsupported evidence-plan completion schema version.")
        required = (
            ("completion_input_id", self.completion_input_id),
            ("source_plan_id", self.source_plan_id),
            ("reference_id", self.reference_id),
            ("declaration_source", self.declaration_source),
        )
        for field, value in required:
            if not isinstance(value, str):
                raise TypeError(
                    f"Evidence-plan completion field {field} must be a string."
                )
            if not value or value != value.strip():
                raise ValueError(
                    f"Evidence-plan completion field {field} must be an explicit "
                    "non-empty string without surrounding whitespace."
                )
        if not isinstance(
            self.reference_kind,
            EvidencePlanCompletionReferenceKind,
        ):
            raise ValueError("Evidence-plan completion reference kind is invalid.")
        if (
            self.reference_kind is EvidencePlanCompletionReferenceKind.PLAN
            and self.reference_id == self.source_plan_id
        ):
            raise ValueError(
                "Evidence-plan completion reference cannot be the source plan itself."
            )
        if self.user_note is not None:
            if not isinstance(self.user_note, str):
                raise TypeError(
                    "Evidence-plan completion user note must be text or absent."
                )
            if not self.user_note or self.user_note != self.user_note.strip():
                raise ValueError(
                    "Evidence-plan completion user note must be absent or explicit "
                    "text without surrounding whitespace."
                )


@dataclass(frozen=True)
class EvidencePlanCompletionResolution:
    completion_input: EvidencePlanCompletionInput
    source_plan: EvidenceAcquisitionPlan
    reference: ListeningPositionSamplingProtocol | EvidenceAcquisitionPlan
    status: EvidencePlanCompletionResolutionStatus

    def __post_init__(self):
        if not isinstance(self.completion_input, EvidencePlanCompletionInput):
            raise TypeError("Evidence-plan completion input is required.")
        if not isinstance(self.source_plan, EvidenceAcquisitionPlan):
            raise TypeError("Evidence-plan completion source plan is required.")
        if self.source_plan.plan_id != self.completion_input.source_plan_id:
            raise ValueError(
                "Resolved evidence-plan completion source identity is inconsistent."
            )
        expected_type = (
            ListeningPositionSamplingProtocol
            if self.completion_input.reference_kind
            is EvidencePlanCompletionReferenceKind.PROTOCOL
            else EvidenceAcquisitionPlan
        )
        if not isinstance(self.reference, expected_type):
            raise TypeError(
                "Resolved evidence-plan completion reference kind is inconsistent."
            )
        reference_id = (
            self.reference.protocol_id
            if self.completion_input.reference_kind
            is EvidencePlanCompletionReferenceKind.PROTOCOL
            else self.reference.plan_id
        )
        if reference_id != self.completion_input.reference_id:
            raise ValueError(
                "Resolved evidence-plan completion reference identity is inconsistent."
            )
        if self.status is not (
            EvidencePlanCompletionResolutionStatus.REFERENCE_RESOLVED
        ):
            raise ValueError(
                "Evidence-plan completion resolution status is invalid."
            )
