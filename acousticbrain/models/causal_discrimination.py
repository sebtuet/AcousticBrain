from dataclasses import dataclass
from enum import Enum
from math import isfinite


class CausalProtocolStatus(Enum):
    INCOMPLETE = "INCOMPLETE"
    ACTIVE = "ACTIVE"
    DEFERRED = "DEFERRED"
    CONTRADICTORY = "CONTRADICTORY"


class CausalDiscriminationOutcome(Enum):
    INCONCLUSIVE = "INCONCLUSIVE"
    DISCRIMINATED = "DISCRIMINATED"
    CONTRADICTORY = "CONTRADICTORY"


class CausalDiscriminationDecisionStatus(Enum):
    DEFERRED = "DEFERRED"


class CausalDiscriminationDecisionReason(Enum):
    USER_DECISION = "USER_DECISION"


class CausalTrajectoryCode(Enum):
    ANOMALY_FOLLOWS_LOUDSPEAKER = "ANOMALY_FOLLOWS_LOUDSPEAKER"
    ANOMALY_FOLLOWS_SIGNAL_CHAIN = "ANOMALY_FOLLOWS_SIGNAL_CHAIN"
    ANOMALY_REMAINS_WITH_ROOM_SIDE = "ANOMALY_REMAINS_WITH_ROOM_SIDE"
    DISCRIMINATION_INCONCLUSIVE = "DISCRIMINATION_INCONCLUSIVE"


class CausalTrajectoryStatus(Enum):
    COMPATIBLE = "COMPATIBLE"
    CONTRADICTED = "CONTRADICTED"


@dataclass(frozen=True)
class CausalProtocolStep:
    protocol_code: str
    step_code: str
    step_index: int
    experiment_id: str
    controlled_variable_codes: tuple[str, ...]
    changed_variable_codes: tuple[str, ...]
    unknown_variable_codes: tuple[str, ...]
    observation_codes: tuple[str, ...]

    def __post_init__(self):
        for value in (self.protocol_code, self.step_code, self.experiment_id):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Causal protocol step identifiers are required.")
        if (
            not isinstance(self.step_index, int)
            or isinstance(self.step_index, bool)
            or self.step_index < 0
        ):
            raise ValueError("Causal protocol step index must be non-negative.")
        collections = (
            self.controlled_variable_codes,
            self.changed_variable_codes,
            self.unknown_variable_codes,
            self.observation_codes,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Causal protocol step collections must be tuples.")
        variables = (
            set(self.controlled_variable_codes),
            set(self.changed_variable_codes),
            set(self.unknown_variable_codes),
        )
        if any(left & right for index, left in enumerate(variables)
               for right in variables[index + 1:]):
            raise ValueError("Controlled, changed and unknown variables must be disjoint.")
        if any(
            len(values) != len(set(values))
            or any(not isinstance(value, str) or not value for value in values)
            for values in collections
        ):
            raise ValueError("Causal protocol step codes must be unique and non-empty.")


@dataclass(frozen=True)
class CausalDiscriminationDecision:
    protocol_code: str
    discrimination_code: str
    status: CausalDiscriminationDecisionStatus
    reason: CausalDiscriminationDecisionReason
    experiment_id: str

    def __post_init__(self):
        for value in (
            self.protocol_code,
            self.discrimination_code,
            self.experiment_id,
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Causal discrimination decision identifiers are required.")
        if not isinstance(self.status, CausalDiscriminationDecisionStatus):
            raise ValueError("Causal discrimination decision status is invalid.")
        if not isinstance(self.reason, CausalDiscriminationDecisionReason):
            raise ValueError("Causal discrimination decision reason is invalid.")


@dataclass(frozen=True)
class CausalTrajectoryAssessment:
    trajectory_code: CausalTrajectoryCode
    status: CausalTrajectoryStatus
    support_score: float
    supporting_observation_codes: tuple[str, ...]
    counter_evidence_codes: tuple[str, ...]
    remaining_ambiguity_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]

    def __post_init__(self):
        if not isfinite(self.support_score) or not 0.0 <= self.support_score <= 100.0:
            raise ValueError("Causal trajectory support score must be bounded.")
        collections = (
            self.supporting_observation_codes,
            self.counter_evidence_codes,
            self.remaining_ambiguity_codes,
            self.applied_rule_codes,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Causal trajectory collections must be tuples.")
        expected = (
            CausalTrajectoryStatus.CONTRADICTED
            if self.counter_evidence_codes
            else CausalTrajectoryStatus.COMPATIBLE
        )
        if self.status is not expected:
            raise ValueError("Causal trajectory status must match counter-evidence.")


@dataclass(frozen=True)
class CausalDiscriminationTrace:
    trace_id: str
    protocol_code: str
    experiment_ids: tuple[str, ...]
    step_codes: tuple[str, ...]
    changed_variable_codes: tuple[str, ...]
    controlled_variable_codes: tuple[str, ...]
    observation_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]
    trajectory_codes: tuple[str, ...]
    resolved_discrimination_codes: tuple[str, ...]
    remaining_discrimination_codes: tuple[str, ...]
    decision_codes: tuple[str, ...]


@dataclass(frozen=True)
class CausalDiscriminationAnalysis:
    protocol_code: str
    status: CausalProtocolStatus
    outcome: CausalDiscriminationOutcome
    completed_steps: tuple[CausalProtocolStep, ...]
    remaining_step_codes: tuple[str, ...]
    deferred_step_codes: tuple[str, ...]
    trajectory_assessments: tuple[CausalTrajectoryAssessment, ...]
    resolved_discrimination_codes: tuple[str, ...]
    remaining_discrimination_codes: tuple[str, ...]
    new_ambiguity_codes: tuple[str, ...]
    lost_ambiguity_codes: tuple[str, ...]
    discrimination_decisions: tuple[CausalDiscriminationDecision, ...]
    recommended_next_protocol: str | None
    applied_rule_codes: tuple[str, ...]
    trace: CausalDiscriminationTrace
    detailed_traceability: bool = False

    def __post_init__(self):
        collections = (
            self.completed_steps,
            self.remaining_step_codes,
            self.deferred_step_codes,
            self.trajectory_assessments,
            self.resolved_discrimination_codes,
            self.remaining_discrimination_codes,
            self.new_ambiguity_codes,
            self.lost_ambiguity_codes,
            self.discrimination_decisions,
            self.applied_rule_codes,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Causal discrimination collections must be tuples.")
        indices = tuple(item.step_index for item in self.completed_steps)
        if indices != tuple(sorted(indices)) or len(indices) != len(set(indices)):
            raise ValueError("Completed causal steps must be uniquely ordered.")
