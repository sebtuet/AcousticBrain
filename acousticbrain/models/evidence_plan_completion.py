from dataclasses import dataclass
from enum import Enum

from .deterministic_corrective_action import DeterministicCorrectiveAction
from .evidence_acquisition import EvidenceAcquisitionPlan, EvidenceAcquisitionStatus
from .listening_position_sampling_protocol import (
    ListeningPositionSamplingProtocol,
)


class EvidencePlanCompletionReferenceKind(Enum):
    PROTOCOL = "PROTOCOL"
    PLAN = "PLAN"


class EvidencePlanCompletionResolutionStatus(Enum):
    REFERENCE_RESOLVED = "REFERENCE_RESOLVED"


class EvidencePlanCompletionCompatibilityStatus(Enum):
    REFERENCE_COMPATIBLE = "REFERENCE_COMPATIBLE"


class DerivedEvidencePlanStatus(Enum):
    DERIVED_PLAN_READY = "DERIVED_PLAN_READY"


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


@dataclass(frozen=True)
class EvidencePlanCompletionCompatibility:
    resolution: EvidencePlanCompletionResolution
    source_action: DeterministicCorrectiveAction
    authority_id: str
    authority_version: int
    status: EvidencePlanCompletionCompatibilityStatus

    AUTHORITY_ID = "deterministic_corrective_action.compatible_reference.v1"
    AUTHORITY_VERSION = 1

    def __post_init__(self):
        if not isinstance(self.resolution, EvidencePlanCompletionResolution):
            raise TypeError("Evidence-plan completion resolution is required.")
        if not isinstance(self.source_action, DeterministicCorrectiveAction):
            raise TypeError("Evidence-plan completion source action is required.")
        if (
            self.source_action.action_id
            != self.resolution.source_plan.corrective_action_id
        ):
            raise ValueError(
                "Evidence-plan completion compatibility action is inconsistent."
            )
        if (
            self.resolution.source_plan.reasoning_id
            not in self.source_action.source_reasoning_ids
        ):
            raise ValueError(
                "Evidence-plan completion compatibility reasoning is inconsistent."
            )
        completion_input = self.resolution.completion_input
        compatible_ids = (
            self.source_action.compatible_protocol_ids
            if completion_input.reference_kind
            is EvidencePlanCompletionReferenceKind.PROTOCOL
            else self.source_action.compatible_plan_ids
        )
        if completion_input.reference_id not in compatible_ids:
            raise ValueError(
                "Evidence-plan completion reference is not associated with the "
                "source action."
            )
        if self.authority_id != self.AUTHORITY_ID:
            raise ValueError(
                "Evidence-plan completion compatibility authority is invalid."
            )
        if self.authority_version != self.AUTHORITY_VERSION:
            raise ValueError(
                "Evidence-plan completion compatibility authority version is invalid."
            )
        if self.status is not (
            EvidencePlanCompletionCompatibilityStatus.REFERENCE_COMPATIBLE
        ):
            raise ValueError(
                "Evidence-plan completion compatibility status is invalid."
            )


@dataclass(frozen=True)
class DerivedEvidenceAcquisitionPlan:
    plan: EvidenceAcquisitionPlan
    source_plan: EvidenceAcquisitionPlan
    source_plan_id: str
    completion_input_id: str
    reference_kind: EvidencePlanCompletionReferenceKind
    reference_id: str
    compatibility_authority_id: str
    compatibility_authority_version: int
    reference_parameter_codes: tuple[str, ...]
    reference_contract_fingerprint: str
    contract_id: str
    contract_version: int
    status: DerivedEvidencePlanStatus

    CONTRACT_ID = "acousticbrain.evidence_plan_completion_input.v1"
    CONTRACT_VERSION = 1
    MISSING_INPUT = "compatible_protocol_or_plan_id"

    def __post_init__(self):
        if not isinstance(self.plan, EvidenceAcquisitionPlan):
            raise TypeError("Derived evidence-acquisition plan is required.")
        if not isinstance(self.source_plan, EvidenceAcquisitionPlan):
            raise TypeError("Derived source evidence-acquisition plan is required.")
        if self.source_plan.status is not EvidenceAcquisitionStatus.BLOCKED:
            raise ValueError("Derived evidence plan source must remain BLOCKED.")
        if self.plan.status is not EvidenceAcquisitionStatus.READY:
            raise ValueError("Derived evidence plan must be READY.")
        if self.plan.plan_id == self.source_plan.plan_id:
            raise ValueError("Derived evidence plan requires a new plan id.")
        if self.source_plan_id != self.source_plan.plan_id:
            raise ValueError("Derived evidence plan source identity is inconsistent.")
        if not isinstance(self.reference_kind, EvidencePlanCompletionReferenceKind):
            raise ValueError("Derived evidence plan reference kind is invalid.")
        protected = (
            "reasoning_id",
            "corrective_action_id",
            "evidence_weight_id",
            "blocking_factor_ids",
            "objective",
            "test_type",
            "instructions",
            "controlled_variables",
            "independent_variables",
            "measurements_to_capture",
            "expected_observations",
            "success_criteria",
            "failure_criteria",
            "resulting_evidence_targets",
            "priority",
            "estimated_effort",
            "limitations",
            "channel_isolation_evaluation_criteria",
        )
        changed = tuple(
            field
            for field in protected
            if getattr(self.plan, field) != getattr(self.source_plan, field)
        )
        if changed:
            raise ValueError(
                "Derived evidence plan changes protected fields: "
                + ", ".join(changed)
            )
        reference_requirement = (
            f"resolved_reference:{self.reference_kind.value}:{self.reference_id}"
        )
        expected_inputs = tuple(sorted((
            *(
                value for value in self.source_plan.required_inputs
                if value != self.MISSING_INPUT
            ),
            reference_requirement,
        )))
        if self.plan.required_inputs != expected_inputs:
            raise ValueError(
                "Derived evidence plan required inputs are inconsistent."
            )
        strings = (
            self.completion_input_id,
            self.reference_id,
            self.compatibility_authority_id,
            self.reference_contract_fingerprint,
            self.contract_id,
        )
        if any(not isinstance(value, str) or not value for value in strings):
            raise ValueError("Derived evidence plan provenance is incomplete.")
        if (
            self.compatibility_authority_id
            != EvidencePlanCompletionCompatibility.AUTHORITY_ID
            or not isinstance(self.compatibility_authority_version, int)
            or isinstance(self.compatibility_authority_version, bool)
            or self.compatibility_authority_version
            != EvidencePlanCompletionCompatibility.AUTHORITY_VERSION
            or not isinstance(self.contract_version, int)
            or isinstance(self.contract_version, bool)
            or self.contract_id != self.CONTRACT_ID
            or self.contract_version != self.CONTRACT_VERSION
        ):
            raise ValueError("Derived evidence plan contract provenance is invalid.")
        if (
            not isinstance(self.reference_parameter_codes, tuple)
            or not self.reference_parameter_codes
            or len(self.reference_parameter_codes)
            != len(set(self.reference_parameter_codes))
            or any(
                not isinstance(value, str) or not value
                for value in self.reference_parameter_codes
            )
        ):
            raise ValueError(
                "Derived evidence plan reference parameters are incomplete."
            )
        if (
            len(self.reference_contract_fingerprint) != 64
            or any(
                value not in "0123456789abcdef"
                for value in self.reference_contract_fingerprint
            )
        ):
            raise ValueError(
                "Derived evidence plan reference fingerprint is invalid."
            )
        if self.status is not DerivedEvidencePlanStatus.DERIVED_PLAN_READY:
            raise ValueError("Derived evidence plan status is invalid.")
