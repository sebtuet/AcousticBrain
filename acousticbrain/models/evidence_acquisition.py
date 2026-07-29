from dataclasses import dataclass
from enum import Enum

from .channel_isolation_plan_result import (
    ChannelIsolationEvaluationCriterion,
)

class EvidenceAcquisitionTestType(Enum):
    REPEAT_MEASUREMENT = "REPEAT_MEASUREMENT"
    CHANNEL_ISOLATION = "CHANNEL_ISOLATION"
    CONTROLLED_SPEAKER_DISPLACEMENT = "CONTROLLED_SPEAKER_DISPLACEMENT"
    CONTROLLED_MICROPHONE_DISPLACEMENT = "CONTROLLED_MICROPHONE_DISPLACEMENT"
    GEOMETRY_ACQUISITION = "GEOMETRY_ACQUISITION"
    PROTOCOL_EXECUTION = "PROTOCOL_EXECUTION"
    ADDITIONAL_OBSERVATION = "ADDITIONAL_OBSERVATION"
    COMPARATIVE_MEASUREMENT = "COMPARATIVE_MEASUREMENT"
    PARAMETER_COMPLETION = "PARAMETER_COMPLETION"


class EvidenceAcquisitionPriority(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EvidenceAcquisitionEffort(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EvidenceAcquisitionStatus(Enum):
    PROPOSED = "PROPOSED"
    READY = "READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class EvidenceAcquisitionPlan:
    plan_id: str
    reasoning_id: str
    corrective_action_id: str
    evidence_weight_id: str
    blocking_factor_ids: tuple[str, ...]
    objective: str
    test_type: EvidenceAcquisitionTestType
    instructions: tuple[str, ...]
    required_inputs: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    independent_variables: tuple[str, ...]
    measurements_to_capture: tuple[str, ...]
    expected_observations: tuple[str, ...]
    success_criteria: tuple[str, ...]
    failure_criteria: tuple[str, ...]
    resulting_evidence_targets: tuple[str, ...]
    priority: EvidenceAcquisitionPriority
    estimated_effort: EvidenceAcquisitionEffort
    status: EvidenceAcquisitionStatus
    limitations: tuple[str, ...]
    channel_isolation_evaluation_criteria: tuple[
        ChannelIsolationEvaluationCriterion,
        ...,
    ] = ()

    _PERMANENT_LANGUAGE = (
        "permanently",
        "définitivement",
        "final placement",
        "placement final",
        "guaranteed improvement",
        "amélioration garantie",
    )

    def __post_init__(self):
        identities = (
            self.plan_id,
            self.reasoning_id,
            self.corrective_action_id,
            self.evidence_weight_id,
            self.objective,
        )
        if any(not isinstance(value, str) or not value for value in identities):
            raise ValueError("Evidence acquisition plans require stable identities.")
        enums = (
            (self.test_type, EvidenceAcquisitionTestType),
            (self.priority, EvidenceAcquisitionPriority),
            (self.estimated_effort, EvidenceAcquisitionEffort),
            (self.status, EvidenceAcquisitionStatus),
        )
        if any(not isinstance(value, kind) for value, kind in enums):
            raise ValueError("Evidence acquisition plan enum value is invalid.")
        string_collections = (
            self.blocking_factor_ids,
            self.instructions,
            self.required_inputs,
            self.controlled_variables,
            self.independent_variables,
            self.measurements_to_capture,
            self.expected_observations,
            self.success_criteria,
            self.failure_criteria,
            self.resulting_evidence_targets,
            self.limitations,
        )
        collections = (
            *string_collections,
            self.channel_isolation_evaluation_criteria,
        )
        if any(not isinstance(values, tuple) for values in collections):
            raise ValueError("Evidence acquisition collections must be tuples.")
        if not self.blocking_factor_ids:
            raise ValueError("An evidence acquisition plan requires a blocking factor.")
        if not self.instructions:
            raise ValueError("An evidence acquisition plan requires instructions.")
        if not self.success_criteria:
            raise ValueError("An evidence acquisition plan requires success criteria.")
        if not self.resulting_evidence_targets:
            raise ValueError("An evidence acquisition plan requires evidence targets.")
        if any(
            len(values) != len(set(values))
            or any(not isinstance(value, str) or not value for value in values)
            for values in string_collections
        ):
            raise ValueError("Evidence acquisition values must be unique strings.")
        if any(
            not isinstance(value, ChannelIsolationEvaluationCriterion)
            for value in self.channel_isolation_evaluation_criteria
        ):
            raise ValueError(
                "Channel isolation evaluation criteria have an invalid type."
            )
        criterion_ids = tuple(
            value.criterion_id
            for value in self.channel_isolation_evaluation_criteria
        )
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError(
                "Channel isolation evaluation criterion ids must be unique."
            )
        if (
            self.test_type is not EvidenceAcquisitionTestType.CHANNEL_ISOLATION
            and self.channel_isolation_evaluation_criteria
        ):
            raise ValueError(
                "Only CHANNEL_ISOLATION plans may declare evaluation criteria."
            )
        language = " ".join((self.objective, *self.instructions, *self.success_criteria)).casefold()
        if any(value in language for value in self._PERMANENT_LANGUAGE):
            raise ValueError("Evidence acquisition cannot prescribe permanent correction.")
        if self.test_type is EvidenceAcquisitionTestType.CONTROLLED_SPEAKER_DISPLACEMENT:
            required = ("temporary", "return to the initial position", "protocol-defined")
            if any(value not in language for value in required):
                raise ValueError("Controlled displacement must be reversible and protocol-defined.")

    def to_dict(self):
        return {
            "plan_id": self.plan_id,
            "reasoning_id": self.reasoning_id,
            "corrective_action_id": self.corrective_action_id,
            "evidence_weight_id": self.evidence_weight_id,
            "blocking_factor_ids": self.blocking_factor_ids,
            "objective": self.objective,
            "test_type": self.test_type.value,
            "instructions": self.instructions,
            "required_inputs": self.required_inputs,
            "controlled_variables": self.controlled_variables,
            "independent_variables": self.independent_variables,
            "measurements_to_capture": self.measurements_to_capture,
            "expected_observations": self.expected_observations,
            "success_criteria": self.success_criteria,
            "failure_criteria": self.failure_criteria,
            "resulting_evidence_targets": self.resulting_evidence_targets,
            "priority": self.priority.value,
            "estimated_effort": self.estimated_effort.value,
            "status": self.status.value,
            "limitations": self.limitations,
            "channel_isolation_evaluation_criteria": tuple(
                value.to_dict()
                for value in self.channel_isolation_evaluation_criteria
            ),
        }


@dataclass(frozen=True)
class EvidenceAcquisitionPlanSynthesis:
    plans: tuple[EvidenceAcquisitionPlan, ...] = ()

    def __post_init__(self):
        if not isinstance(self.plans, tuple) or any(
            not isinstance(value, EvidenceAcquisitionPlan) for value in self.plans
        ):
            raise ValueError("Evidence acquisition synthesis requires immutable plans.")
        identifiers = tuple(value.plan_id for value in self.plans)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Evidence acquisition plan ids must be unique.")
