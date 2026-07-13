from dataclasses import dataclass
from enum import Enum
from math import isfinite


ComparisonValue = str | int | float | bool


class ExperimentComparisonType(Enum):
    LOCAL = "LOCAL"
    CUMULATIVE = "CUMULATIVE"


class ComparisonEligibilityStatus(Enum):
    COMPARABLE = "COMPARABLE"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class ComparisonIneligibilityReason(Enum):
    EXPERIMENT_INCOMPLETE = "EXPERIMENT_INCOMPLETE"
    NO_USABLE_MEASUREMENT = "NO_USABLE_MEASUREMENT"
    READINESS_BLOCKED = "READINESS_BLOCKED"
    INCOMPATIBLE_UNIT = "INCOMPATIBLE_UNIT"
    INCOMPATIBLE_FAMILY = "INCOMPATIBLE_FAMILY"
    INCOMPATIBLE_SEMANTICS = "INCOMPATIBLE_SEMANTICS"
    AMBIGUOUS_PARENT = "AMBIGUOUS_PARENT"
    UNKNOWN_PARENT = "UNKNOWN_PARENT"
    INVALID_CHRONOLOGY = "INVALID_CHRONOLOGY"
    REQUIRED_FACT_UNAVAILABLE = "REQUIRED_FACT_UNAVAILABLE"
    IDENTICAL_CONTENT = "IDENTICAL_CONTENT"
    INSUFFICIENT_BEFORE_DATA = "INSUFFICIENT_BEFORE_DATA"
    INSUFFICIENT_AFTER_DATA = "INSUFFICIENT_AFTER_DATA"


class ExperimentEvolutionOutcome(Enum):
    STRONGER = "STRONGER"
    WEAKER = "WEAKER"
    UNCHANGED = "UNCHANGED"
    INCONCLUSIVE = "INCONCLUSIVE"
    CONTRADICTED = "CONTRADICTED"


class ExperimentFactChange(Enum):
    IMPROVED = "IMPROVED"
    DEGRADED = "DEGRADED"
    CHANGED = "CHANGED"
    UNCHANGED = "UNCHANGED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ComparableExperimentFact:
    code: str
    value: ComparisonValue | None
    unit: str
    family: str
    semantic: str
    source_analysis: str
    threshold: float
    higher_is_better: bool | None
    readiness: str = "AVAILABLE"
    provenance_codes: tuple[str, ...] = ()

    def __post_init__(self):
        if any(not isinstance(value, str) or not value for value in (
            self.code, self.unit, self.family, self.semantic, self.source_analysis
        )):
            raise ValueError("Comparable fact identifiers are required.")
        if not isfinite(self.threshold) or self.threshold < 0.0:
            raise ValueError("Comparable fact threshold must be non-negative.")
        if not isinstance(self.provenance_codes, tuple):
            raise ValueError("Comparable fact provenance must be a tuple.")


@dataclass(frozen=True)
class ExperimentFactDelta:
    fact_code: str
    before: ComparisonValue | None
    after: ComparisonValue | None
    delta: float | None
    unit: str
    change: ExperimentFactChange
    threshold: float
    source_analysis_codes: tuple[str, ...]


@dataclass(frozen=True)
class ObservedExperimentFact:
    code: str
    source_fact_codes: tuple[str, ...]
    provenance_codes: tuple[str, ...]


@dataclass(frozen=True)
class ExperimentCounterFact:
    code: str
    source_fact_codes: tuple[str, ...]
    provenance_codes: tuple[str, ...]


@dataclass(frozen=True)
class UnresolvedDiscrimination:
    code: str
    required_change_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExperimentComparisonTrace:
    trace_id: str
    comparison_type: ExperimentComparisonType
    before_experiment_id: str
    after_experiment_id: str
    before_file_hash: str
    after_file_hash: str
    before_fact_codes: tuple[str, ...]
    after_fact_codes: tuple[str, ...]
    delta_fact_codes: tuple[str, ...]
    observed_fact_codes: tuple[str, ...]
    hypothesis_code: str | None
    evolution_outcome: ExperimentEvolutionOutcome
    unresolved_discrimination_codes: tuple[str, ...]


@dataclass(frozen=True)
class ExperimentEvolutionResult:
    result_id: str
    before_experiment_id: str
    after_experiment_id: str
    comparison_type: ExperimentComparisonType
    source_protocol_id: str | None
    source_hypothesis_code: str | None
    initial_hypothesis_status: str | None
    outcome: ExperimentEvolutionOutcome
    eligibility: ComparisonEligibilityStatus
    ineligibility_reasons: tuple[ComparisonIneligibilityReason, ...]
    fact_deltas: tuple[ExperimentFactDelta, ...]
    observed_facts: tuple[ObservedExperimentFact, ...]
    counter_facts: tuple[ExperimentCounterFact, ...]
    unavailable_fact_codes: tuple[str, ...]
    unresolved_discriminations: tuple[UnresolvedDiscrimination, ...]
    applied_rule_codes: tuple[str, ...]
    applied_threshold_codes: tuple[str, ...]
    technical_confidence: float | None
    provenance_codes: tuple[str, ...]
    trace: ExperimentComparisonTrace

    def __post_init__(self):
        collections = (
            self.ineligibility_reasons, self.fact_deltas, self.observed_facts,
            self.counter_facts, self.unavailable_fact_codes,
            self.unresolved_discriminations, self.applied_rule_codes,
            self.applied_threshold_codes, self.provenance_codes,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Evolution-result collections must be tuples.")
        if self.technical_confidence is not None and (
            not isfinite(self.technical_confidence)
            or not 0.0 <= self.technical_confidence <= 100.0
        ):
            raise ValueError("Evolution confidence must be bounded.")


@dataclass(frozen=True)
class ExperimentComparisonSequence:
    chronology: tuple[str, ...]
    local_comparisons: tuple[ExperimentEvolutionResult, ...]
    cumulative_comparisons: tuple[ExperimentEvolutionResult, ...]


@dataclass(frozen=True)
class ExperimentComparisonAnalysis:
    sequence: ExperimentComparisonSequence
    source_analysis_codes: tuple[str, ...]
    detailed_traceability: bool = False
