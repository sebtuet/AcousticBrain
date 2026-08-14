from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedSessionIteration:
    number: int
    hypothesis_code: str
    experiment_label: str
    before_state_id: str
    after_state_id: str | None
    improved_fact_codes: tuple[str, ...]
    degraded_fact_codes: tuple[str, ...]
    hypothesis_result: str | None


@dataclass(frozen=True)
class PresentedSessionTraceChain:
    measurement_name: str
    source_state_id: str
    fact_codes: tuple[str, ...]
    correlation_codes: tuple[str, ...]
    hypothesis_code: str
    protocol_id: str
    new_state_id: str
    comparison_id: str
    evolution_result: str
    progression_id: str


@dataclass(frozen=True)
class PresentedOptimizationSession:
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
    iterations: tuple[PresentedSessionIteration, ...]
    trace_chains: tuple[PresentedSessionTraceChain, ...]
    detailed_traceability: bool = False

    def to_dict(self):
        return asdict(self)


class OptimizationSessionPresenter:
    """Projection pure des résultats de session calculés en amont."""

    def present(self, context) -> PresentedOptimizationSession | None:
        session = getattr(context, "optimization_session", None)
        analysis = getattr(context, "optimization_session_analysis", None)
        if session is None or analysis is None:
            return None
        return PresentedOptimizationSession(
            session_id=analysis.session_id,
            current_iteration=analysis.current_iteration,
            completed_experiments=analysis.completed_experiments,
            open_hypotheses=analysis.open_hypotheses,
            reinforced_hypotheses=analysis.reinforced_hypotheses,
            refuted_hypotheses=analysis.refuted_hypotheses,
            global_gain=analysis.global_gain,
            main_improvements=analysis.main_improvements,
            main_degradations=analysis.main_degradations,
            pending_experiment=analysis.pending_experiment,
            iterations=tuple(
                PresentedSessionIteration(
                    number=item.number,
                    hypothesis_code=item.protocol.hypothesis_code,
                    experiment_label=item.protocol.label,
                    before_state_id=item.before_state_id,
                    after_state_id=item.after_state_id,
                    improved_fact_codes=tuple(
                        change.fact_code
                        for change in item.comparison.improved_facts
                    ) if item.comparison else (),
                    degraded_fact_codes=tuple(
                        change.fact_code
                        for change in item.comparison.degraded_facts
                    ) if item.comparison else (),
                    hypothesis_result=(
                        item.comparison.hypothesis_evolution.result.value
                        if item.comparison else None
                    ),
                )
                for item in session.iterations
            ),
            trace_chains=tuple(
                PresentedSessionTraceChain(**asdict(item))
                for item in analysis.trace_chains
            ),
            detailed_traceability=session.detailed_traceability,
        )
