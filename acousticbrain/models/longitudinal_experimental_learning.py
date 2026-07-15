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
class LongitudinalAmbiguityProvenance:
    ambiguity_code: str
    source_analysis_code: str
    source_id: str
    protocol_code: str
    source_experiment_codes: tuple[str, ...]

    def __post_init__(self):
        identifiers = (
            self.ambiguity_code,
            self.source_analysis_code,
            self.source_id,
            self.protocol_code,
        )
        if any(not isinstance(value, str) or not value for value in identifiers):
            raise ValueError("Ambiguity provenance identifiers are required.")
        if not isinstance(self.source_experiment_codes, tuple):
            raise ValueError("Ambiguity provenance experiments must be a tuple.")
        if self.source_experiment_codes != tuple(sorted(set(
            self.source_experiment_codes
        ))):
            raise ValueError(
                "Ambiguity provenance experiments must be uniquely ordered."
            )


@dataclass(frozen=True)
class LongitudinalExperimentalLearningState:
    state_id: str
    hypothesis_code: str
    protocol_codes: tuple[str, ...]
    historical_context_experiment_codes: tuple[str, ...]
    evidence_contributing_experiment_codes: tuple[str, ...]
    campaign_source_experiment_codes: tuple[str, ...]
    discrimination_source_experiment_codes: tuple[str, ...]
    historical_experiment_declaration_statuses: tuple[tuple[str, str], ...]
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
    resolved_ambiguity_provenance: tuple[LongitudinalAmbiguityProvenance, ...]
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
            self.historical_context_experiment_codes,
            self.evidence_contributing_experiment_codes,
            self.campaign_source_experiment_codes,
            self.discrimination_source_experiment_codes,
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
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Longitudinal learning collections must be tuples.")
        if any(len(value) != len(set(value)) for value in collections):
            raise ValueError("Longitudinal learning codes must be unique.")
        structured_collections = (
            self.historical_experiment_declaration_statuses,
            self.resolved_ambiguity_provenance,
            self.evidence_summary,
            self.provenance,
        )
        if any(not isinstance(value, tuple) for value in structured_collections):
            raise ValueError("Longitudinal structured collections must be tuples.")
        if tuple(sorted(
            self.historical_experiment_declaration_statuses
        )) != self.historical_experiment_declaration_statuses:
            raise ValueError(
                "Historical declaration statuses must be deterministically ordered."
            )
        ambiguity_codes = tuple(
            item.ambiguity_code for item in self.resolved_ambiguity_provenance
        )
        if ambiguity_codes != tuple(sorted(set(ambiguity_codes))):
            raise ValueError(
                "Resolved ambiguity provenance must be uniquely ordered."
            )
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
