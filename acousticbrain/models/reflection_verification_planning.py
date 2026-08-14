from dataclasses import dataclass
from enum import Enum


class ReflectionVerificationMethod(Enum):
    TEMPORARY_MASK = "TEMPORARY_MASK"


class ReflectionVerificationExecutionStatus(Enum):
    NOT_EXECUTED = "NOT_EXECUTED"


class ReflectionVerificationCausalityStatus(Enum):
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class ReflectionVerificationImpact(Enum):
    NONE = "NONE"


class ReflectionVerificationExclusionReason(Enum):
    GEOMETRICALLY_REJECTED = "GEOMETRICALLY_REJECTED"


@dataclass(frozen=True)
class ReflectionCandidateVerificationProposal:
    proposal_id: str
    source_candidate_id: str
    proposal_order: int
    correlation_id: str
    path_id: str
    surface_id: str
    region_id: str | None
    observed_event_id: str
    target_kind: str
    target_id: str
    method: ReflectionVerificationMethod
    reference_condition_code: str
    intervention_condition_code: str
    controlled_variable_codes: tuple[str, ...]
    changed_variable_codes: tuple[str, ...]
    observable_fact_codes: tuple[str, ...]
    supporting_outcome_codes: tuple[str, ...]
    counter_outcome_codes: tuple[str, ...]
    source_evidence_codes: tuple[str, ...]
    source_provenance_codes: tuple[str, ...]
    planning_rule_codes: tuple[str, ...]
    execution_status: ReflectionVerificationExecutionStatus
    causality_status: ReflectionVerificationCausalityStatus
    eligibility_impact: ReflectionVerificationImpact
    recommendation_impact: ReflectionVerificationImpact
    limitations: tuple[str, ...]

    def __post_init__(self):
        identifiers = (
            self.proposal_id,
            self.source_candidate_id,
            self.correlation_id,
            self.path_id,
            self.surface_id,
            self.observed_event_id,
            self.target_kind,
            self.target_id,
            self.reference_condition_code,
            self.intervention_condition_code,
        )
        if any(not isinstance(value, str) or not value.strip() for value in identifiers):
            raise ValueError("Reflection verification identifiers are required.")
        if self.region_id is not None and (
            not isinstance(self.region_id, str) or not self.region_id.strip()
        ):
            raise ValueError("Reflection verification region identifiers cannot be empty.")
        if not isinstance(self.proposal_order, int) or isinstance(
            self.proposal_order, bool
        ) or self.proposal_order < 1:
            raise ValueError("Reflection verification order must be positive.")
        if not isinstance(self.method, ReflectionVerificationMethod):
            raise ValueError("Reflection verification method is invalid.")
        collections = (
            self.controlled_variable_codes,
            self.changed_variable_codes,
            self.observable_fact_codes,
            self.supporting_outcome_codes,
            self.counter_outcome_codes,
            self.source_evidence_codes,
            self.source_provenance_codes,
            self.planning_rule_codes,
            self.limitations,
        )
        if any(
            not isinstance(collection, tuple)
            or any(not isinstance(item, str) or not item.strip() for item in collection)
            or len(collection) != len(set(collection))
            for collection in collections
        ):
            raise ValueError("Reflection verification trace fields must be unique tuples.")
        if not self.controlled_variable_codes or not self.changed_variable_codes:
            raise ValueError("Controlled verification requires explicit variables.")
        if set(self.controlled_variable_codes) & set(self.changed_variable_codes):
            raise ValueError("Controlled and changed variables must remain separate.")
        if not self.observable_fact_codes or not self.source_evidence_codes:
            raise ValueError("Reflection verification requires observable provenance.")
        if self.execution_status is not ReflectionVerificationExecutionStatus.NOT_EXECUTED:
            raise ValueError("PR-036 cannot execute reflection verification.")
        if self.causality_status is not ReflectionVerificationCausalityStatus.NOT_ESTABLISHED:
            raise ValueError("PR-036 cannot establish causality.")
        if self.eligibility_impact is not ReflectionVerificationImpact.NONE:
            raise ValueError("PR-036 cannot affect eligibility.")
        if self.recommendation_impact is not ReflectionVerificationImpact.NONE:
            raise ValueError("PR-036 cannot affect recommendations.")


@dataclass(frozen=True)
class ReflectionCandidateVerificationExclusion:
    source_candidate_id: str
    reason: ReflectionVerificationExclusionReason
    source_evidence_codes: tuple[str, ...]
    source_provenance_codes: tuple[str, ...]
    planning_rule_codes: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.source_candidate_id, str) or not self.source_candidate_id.strip():
            raise ValueError("Excluded reflection candidates require an identifier.")
        if self.reason is not ReflectionVerificationExclusionReason.GEOMETRICALLY_REJECTED:
            raise ValueError("Only geometrically rejected candidates may be excluded.")
        for collection in (
            self.source_evidence_codes,
            self.source_provenance_codes,
            self.planning_rule_codes,
        ):
            if not isinstance(collection, tuple) or any(
                not isinstance(item, str) or not item.strip() for item in collection
            ):
                raise ValueError("Reflection exclusion trace fields must be tuples.")


@dataclass(frozen=True)
class ControlledReflectionVerificationPlanningAnalysis:
    proposals: tuple[ReflectionCandidateVerificationProposal, ...]
    exclusions: tuple[ReflectionCandidateVerificationExclusion, ...]
    source_analysis_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]

    def __post_init__(self):
        typed = (
            (self.proposals, ReflectionCandidateVerificationProposal),
            (self.exclusions, ReflectionCandidateVerificationExclusion),
        )
        if any(
            not isinstance(collection, tuple)
            or any(not isinstance(item, expected) for item in collection)
            for collection, expected in typed
        ):
            raise ValueError("Reflection verification planning outputs must be typed tuples.")
        for collection in (self.source_analysis_codes, self.applied_rule_codes):
            if not isinstance(collection, tuple) or any(
                not isinstance(item, str) or not item.strip() for item in collection
            ):
                raise ValueError("Reflection planning trace fields must be tuples.")
        proposal_ids = tuple(item.proposal_id for item in self.proposals)
        source_ids = tuple(item.source_candidate_id for item in self.proposals)
        excluded_ids = tuple(item.source_candidate_id for item in self.exclusions)
        if len(proposal_ids) != len(set(proposal_ids)):
            raise ValueError("Reflection verification proposal identifiers must be unique.")
        if set(source_ids) & set(excluded_ids):
            raise ValueError("A reflection candidate cannot be proposed and excluded.")
