from dataclasses import dataclass
from enum import Enum, IntEnum
from math import isfinite


class ExperimentPlanningStatus(Enum):
    READY = "READY"
    NO_ELIGIBLE_CANDIDATE = "NO_ELIGIBLE_CANDIDATE"


class ExperimentDifficulty(IntEnum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


class ExperimentReversibility(IntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class ExperimentCostCategory(IntEnum):
    FREE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class ExperimentSelectionReason(Enum):
    HIGH_UNCERTAINTY = "HIGH_UNCERTAINTY"
    RESOLVES_MISSING_FACTS = "RESOLVES_MISSING_FACTS"
    DISCRIMINATES_COUNTER_EVIDENCE = "DISCRIMINATES_COUNTER_EVIDENCE"
    DISCRIMINATES_HYPOTHESES = "DISCRIMINATES_HYPOTHESES"
    HIGH_REVERSIBILITY = "HIGH_REVERSIBILITY"
    LOW_DIFFICULTY = "LOW_DIFFICULTY"
    LOW_COST = "LOW_COST"
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    SOURCE_HYPOTHESIS_MISSING = "SOURCE_HYPOTHESIS_MISSING"
    SOURCE_PROTOCOL_MISSING = "SOURCE_PROTOCOL_MISSING"
    INCOMPLETE_PROVENANCE = "INCOMPLETE_PROVENANCE"
    PREREQUISITE_MISSING = "PREREQUISITE_MISSING"
    OBSERVABLE_FACTS_MISSING = "OBSERVABLE_FACTS_MISSING"
    ALREADY_COMPLETED = "ALREADY_COMPLETED"
    HYPOTHESIS_REFUTED = "HYPOTHESIS_REFUTED"
    GEOMETRY_PARAMETER_MISSING = "GEOMETRY_PARAMETER_MISSING"
    NON_REVERSIBLE = "NON_REVERSIBLE"
    USER_DEFERRED = "USER_DEFERRED"


@dataclass(frozen=True)
class ExperimentCandidate:
    candidate_id: str
    hypothesis_code: str
    source_action_code: str | None
    source_protocol_id: str
    hypothesis_status: str
    support_score: float
    confidence: float
    counter_evidence_count: int
    missing_fact_count: int
    informative_value: float
    difficulty: ExperimentDifficulty
    estimated_duration_minutes: int | None
    cost_category: ExperimentCostCategory
    reversibility: ExperimentReversibility
    objective_code: str
    observable_fact_codes: tuple[str, ...]
    discriminated_hypothesis_codes: tuple[str, ...]
    prerequisite_codes: tuple[str, ...]
    unmet_prerequisite_codes: tuple[str, ...]
    selection_reasons: tuple[ExperimentSelectionReason, ...]
    ineligibility_reasons: tuple[ExperimentSelectionReason, ...]
    source_analysis_codes: tuple[str, ...]
    evidence_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]
    eligible: bool

    def __post_init__(self):
        for value in (
            self.candidate_id,
            self.hypothesis_code,
            self.source_protocol_id,
            self.hypothesis_status,
            self.objective_code,
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Experiment candidate identifiers are required.")
        for score in (self.support_score, self.confidence, self.informative_value):
            if not isfinite(score) or not 0.0 <= score <= 100.0:
                raise ValueError("Experiment candidate scores must be bounded.")
        collections = (
            self.observable_fact_codes,
            self.discriminated_hypothesis_codes,
            self.prerequisite_codes,
            self.unmet_prerequisite_codes,
            self.selection_reasons,
            self.ineligibility_reasons,
            self.source_analysis_codes,
            self.evidence_codes,
            self.applied_rule_codes,
        )
        if any(not isinstance(collection, tuple) for collection in collections):
            raise ValueError("Experiment candidate collections must be tuples.")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in (self.counter_evidence_count, self.missing_fact_count)
        ):
            raise ValueError("Experiment candidate counts must be non-negative.")
        if (
            self.estimated_duration_minutes is not None
            and (
                not isinstance(self.estimated_duration_minutes, int)
                or isinstance(self.estimated_duration_minutes, bool)
                or self.estimated_duration_minutes < 0
            )
        ):
            raise ValueError("Experiment duration must be non-negative.")
        if self.eligible == bool(self.ineligibility_reasons):
            raise ValueError("Experiment eligibility and reasons are inconsistent.")


@dataclass(frozen=True)
class ExperimentPlanningTraceLink:
    trace_id: str
    fact_codes: tuple[str, ...]
    evidence_codes: tuple[str, ...]
    hypothesis_code: str
    source_protocol_id: str
    candidate_id: str
    rank: int | None
    recommended: bool
    session_iteration_number: int | None

    def __post_init__(self):
        for collection in (self.fact_codes, self.evidence_codes):
            if not isinstance(collection, tuple):
                raise ValueError("Planning trace collections must be tuples.")
        for value in (self.rank, self.session_iteration_number):
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 1
            ):
                raise ValueError("Planning trace positions must be positive.")


@dataclass(frozen=True)
class ExperimentPlan:
    ordered_candidates: tuple[ExperimentCandidate, ...]
    recommended_candidate: ExperimentCandidate | None
    ineligible_candidates: tuple[ExperimentCandidate, ...]
    applied_rule_codes: tuple[str, ...]
    technical_confidence: float | None
    source_analysis_codes: tuple[str, ...]

    def __post_init__(self):
        for collection in (
            self.ordered_candidates,
            self.ineligible_candidates,
            self.applied_rule_codes,
            self.source_analysis_codes,
        ):
            if not isinstance(collection, tuple):
                raise ValueError("Experiment plan collections must be tuples.")
        if self.technical_confidence is not None and (
            not isfinite(self.technical_confidence)
            or not 0.0 <= self.technical_confidence <= 100.0
        ):
            raise ValueError("Planning confidence must be bounded.")
        if any(not item.eligible for item in self.ordered_candidates):
            raise ValueError("Ordered experiment candidates must be eligible.")
        if any(item.eligible for item in self.ineligible_candidates):
            raise ValueError("Ineligible experiment candidates are inconsistent.")
        if (
            self.recommended_candidate is not None
            and self.recommended_candidate not in self.ordered_candidates
        ):
            raise ValueError("Recommended candidate must belong to the plan.")


@dataclass(frozen=True)
class ExperimentPlanningAnalysis:
    status: ExperimentPlanningStatus
    plan: ExperimentPlan
    trace_links: tuple[ExperimentPlanningTraceLink, ...]

    def __post_init__(self):
        if not isinstance(self.status, ExperimentPlanningStatus):
            raise ValueError("Experiment planning status is invalid.")
        if not isinstance(self.trace_links, tuple):
            raise ValueError("Experiment planning trace links must be a tuple.")
