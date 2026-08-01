from dataclasses import dataclass
from enum import Enum


class EvidencePlanCompletionReferenceKind(Enum):
    PROTOCOL = "PROTOCOL"
    PLAN = "PLAN"


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
