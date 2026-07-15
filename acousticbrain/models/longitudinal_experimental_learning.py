from dataclasses import dataclass
from enum import Enum


class LongitudinalLearningStatus(Enum):
    NOT_TESTED = "NOT_TESTED"
    INSUFFICIENT_DECLARATION = "INSUFFICIENT_DECLARATION"
    INSUFFICIENT_COMPARABILITY = "INSUFFICIENT_COMPARABILITY"
    EVIDENCE_ACCUMULATING = "EVIDENCE_ACCUMULATING"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    STABLE_SUPPORT = "STABLE_SUPPORT"
    STABLE_NON_SUPPORT = "STABLE_NON_SUPPORT"
    DISCRIMINATION_REQUIRED = "DISCRIMINATION_REQUIRED"
    DEFERRED_BY_USER = "DEFERRED_BY_USER"
    EXPERIMENTAL_PATH_EXHAUSTED = "EXPERIMENTAL_PATH_EXHAUSTED"


class ExperimentInformationStatus(Enum):
    NEW_INFORMATION = "NEW_INFORMATION"
    PARTIAL_REPEAT = "PARTIAL_REPEAT"
    EXACT_REPEAT = "EXACT_REPEAT"
    ALREADY_COMPLETED = "ALREADY_COMPLETED"
    BLOCKED_BY_MISSING_DECLARATION = "BLOCKED_BY_MISSING_DECLARATION"
    BLOCKED_BY_NON_COMPARABILITY = "BLOCKED_BY_NON_COMPARABILITY"
    DEFERRED_BY_USER = "DEFERRED_BY_USER"
    STILL_INFORMATIVE = "STILL_INFORMATIVE"


@dataclass(frozen=True)
class LongitudinalExperimentalLearningState:
    state_id: str
    hypothesis_code: str
    protocol_codes: tuple[str, ...]
    experiment_codes: tuple[str, ...]
    comparable_experiment_codes: tuple[str, ...]
    non_comparable_experiment_codes: tuple[str, ...]
    controlled_intervention_codes: tuple[str, ...]
    measurement_repeat_codes: tuple[str, ...]
    unknown_declaration_codes: tuple[str, ...]
    supporting_observation_ids: tuple[str, ...]
    contradicting_observation_ids: tuple[str, ...]
    unchanged_observation_ids: tuple[str, ...]
    inconclusive_observation_ids: tuple[str, ...]
    resolved_ambiguities: tuple[str, ...]
    remaining_ambiguities: tuple[str, ...]
    deferred_discriminations: tuple[str, ...]
    completed_discriminations: tuple[str, ...]
    exhausted_discriminations: tuple[str, ...]
    evidence_summary: tuple[tuple[str, int], ...]
    learning_status: LongitudinalLearningStatus
    next_information_need: str
    causality_status: str
    provenance: tuple[tuple[str, tuple[str, ...]], ...]

    def __post_init__(self):
        if not self.state_id or not self.hypothesis_code:
            raise ValueError("Longitudinal learning identifiers are required.")
        collections = (
            self.protocol_codes,
            self.experiment_codes,
            self.comparable_experiment_codes,
            self.non_comparable_experiment_codes,
            self.controlled_intervention_codes,
            self.measurement_repeat_codes,
            self.unknown_declaration_codes,
            self.supporting_observation_ids,
            self.contradicting_observation_ids,
            self.unchanged_observation_ids,
            self.inconclusive_observation_ids,
            self.resolved_ambiguities,
            self.remaining_ambiguities,
            self.deferred_discriminations,
            self.completed_discriminations,
            self.exhausted_discriminations,
            self.evidence_summary,
            self.provenance,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Longitudinal learning collections must be tuples.")
        code_collections = collections[:-2]
        if any(len(value) != len(set(value)) for value in code_collections):
            raise ValueError("Longitudinal learning codes must be unique.")
        if self.causality_status != "NOT_ESTABLISHED":
            raise ValueError("Longitudinal learning cannot establish causality.")
        if not self.next_information_need:
            raise ValueError("Longitudinal learning requires an explicit information need.")
        if tuple(sorted(self.provenance)) != self.provenance:
            raise ValueError("Longitudinal provenance must be deterministically ordered.")


@dataclass(frozen=True)
class LongitudinalExperimentalLearningAnalysis:
    states: tuple[LongitudinalExperimentalLearningState, ...]
    applied_rule_codes: tuple[str, ...]
    source_analysis_codes: tuple[str, ...]

    def __post_init__(self):
        if not all(isinstance(value, tuple) for value in (
            self.states, self.applied_rule_codes, self.source_analysis_codes
        )):
            raise ValueError("Longitudinal analysis collections must be tuples.")
        hypotheses = tuple(item.hypothesis_code for item in self.states)
        if hypotheses != tuple(sorted(hypotheses)) or len(hypotheses) != len(set(hypotheses)):
            raise ValueError("Longitudinal states must be uniquely ordered by hypothesis.")


@dataclass(frozen=True)
class ExperimentInformationAssessment:
    status: ExperimentInformationStatus
    matching_experiment_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    provenance_codes: tuple[str, ...]

    def __post_init__(self):
        if not all(isinstance(value, tuple) for value in (
            self.matching_experiment_codes,
            self.reason_codes,
            self.provenance_codes,
        )):
            raise ValueError("Information assessment collections must be tuples.")
