from dataclasses import dataclass, field
from enum import Enum
from math import isfinite


SessionValue = str | int | float | bool


class HypothesisEvolutionResult(Enum):
    REINFORCED = "REINFORCED"
    REFUTED = "REFUTED"
    WEAKENED = "WEAKENED"
    UNCHANGED = "UNCHANGED"


@dataclass(frozen=True)
class SessionFact:
    code: str
    source_analysis: str
    value: SessionValue | None
    higher_is_better: bool | None = None


@dataclass(frozen=True)
class SessionCorrelation:
    code: str
    fact_codes: tuple[str, ...]


@dataclass(frozen=True)
class SessionHypothesis:
    code: str
    status: str
    support_score: float
    fact_codes: tuple[str, ...]
    correlation_codes: tuple[str, ...]


@dataclass(frozen=True)
class AcousticBrainState:
    state_id: str
    measurement_name: str
    global_score: float | None
    facts: tuple[SessionFact, ...]
    correlations: tuple[SessionCorrelation, ...]
    hypotheses: tuple[SessionHypothesis, ...]


@dataclass(frozen=True)
class ExperimentProtocol:
    experiment_id: str
    hypothesis_code: str
    action_code: str
    label: str
    fact_codes: tuple[str, ...]

    def __post_init__(self):
        for value, name in (
            (self.experiment_id, "Experiment id"),
            (self.hypothesis_code, "Hypothesis code"),
            (self.action_code, "Action code"),
            (self.label, "Experiment label"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")
        if not isinstance(self.fact_codes, tuple):
            raise ValueError("Experiment fact codes must be a tuple.")


@dataclass(frozen=True)
class FactEvolution:
    fact_code: str
    before: SessionValue | None
    after: SessionValue | None


@dataclass(frozen=True)
class HypothesisEvolution:
    hypothesis_code: str
    before_status: str | None
    after_status: str | None
    before_support_score: float | None
    after_support_score: float | None
    result: HypothesisEvolutionResult


@dataclass(frozen=True)
class ExperimentComparison:
    comparison_id: str
    before_state_id: str
    after_state_id: str
    global_gain: float | None
    improved_facts: tuple[FactEvolution, ...]
    degraded_facts: tuple[FactEvolution, ...]
    hypothesis_evolution: HypothesisEvolution


@dataclass
class OptimizationIteration:
    number: int
    protocol: ExperimentProtocol
    before_state_id: str
    after_state_id: str | None = None
    comparison: ExperimentComparison | None = None

    @property
    def is_completed(self) -> bool:
        return self.after_state_id is not None and self.comparison is not None


@dataclass(frozen=True)
class SessionTraceChain:
    source_state_id: str
    measurement_name: str
    fact_codes: tuple[str, ...]
    correlation_codes: tuple[str, ...]
    hypothesis_code: str
    protocol_id: str
    new_state_id: str
    comparison_id: str
    evolution_result: str
    progression_id: str


@dataclass(frozen=True)
class OptimizationSessionAnalysis:
    session_id: str
    current_iteration: int
    completed_experiments: int
    open_hypotheses: tuple[str, ...]
    reinforced_hypotheses: tuple[str, ...]
    refuted_hypotheses: tuple[str, ...]
    global_gain: float | None
    main_improvements: tuple[str, ...]
    main_degradations: tuple[str, ...]
    pending_experiment: str | None
    trace_chains: tuple[SessionTraceChain, ...]


@dataclass
class OptimizationSession:
    session_id: str
    states: list[AcousticBrainState] = field(default_factory=list)
    iterations: list[OptimizationIteration] = field(default_factory=list)
    analysis: OptimizationSessionAnalysis | None = None
    detailed_traceability: bool = False

    def __post_init__(self):
        if not isinstance(self.session_id, str) or not self.session_id.strip():
            raise ValueError("Session id is required.")

    @property
    def current_state(self) -> AcousticBrainState | None:
        return self.states[-1] if self.states else None

    @property
    def pending_iteration(self) -> OptimizationIteration | None:
        pending = [item for item in self.iterations if not item.is_completed]
        if len(pending) > 1:
            raise ValueError("A session cannot contain several pending iterations.")
        return pending[0] if pending else None


def finite_difference(after: float | None, before: float | None) -> float | None:
    if after is None or before is None:
        return None
    difference = after - before
    return difference if isfinite(difference) else None
