from __future__ import annotations

from dataclasses import dataclass

from acousticbrain.models import (
    AcousticBrainState,
    ExperimentComparison,
    ExperimentProtocol,
    FactEvolution,
    HypothesisEvolution,
    HypothesisEvolutionResult,
    OptimizationIteration,
    OptimizationSession,
    OptimizationSessionAnalysis,
    SessionCorrelation,
    SessionFact,
    SessionHypothesis,
    SessionTraceChain,
)
from acousticbrain.persistence import OptimizationSessionJsonRepository


@dataclass
class OptimizationSessionContext:
    """Contexte explicitement passé au pipeline pour activer une session."""

    session: OptimizationSession
    service: "OptimizationSessionService"

    def record_analysis(self, analysis_context) -> AcousticBrainState:
        return self.service.attach_analysis(self, analysis_context)


class OptimizationSessionService:
    """Cas d'usage applicatifs d'une session, sans analyse de mesure brute."""

    def __init__(self, repository=None):
        self.repository = repository or OptimizationSessionJsonRepository()

    def create(
        self,
        session_id: str,
        *,
        detailed_traceability: bool = False,
    ) -> OptimizationSessionContext:
        session = OptimizationSession(
            session_id=session_id,
            detailed_traceability=detailed_traceability,
        )
        self._refresh_analysis(session)
        return OptimizationSessionContext(session=session, service=self)

    def load(self, path) -> OptimizationSessionContext:
        session = self.repository.load(path)
        self._refresh_analysis(session)
        return OptimizationSessionContext(session=session, service=self)

    def save(self, context: OptimizationSessionContext, path) -> None:
        self._require_context(context)
        self.repository.save(context.session, path)

    def start_iteration(
        self,
        context: OptimizationSessionContext,
        protocol: ExperimentProtocol,
    ) -> OptimizationIteration:
        session = self._require_context(context)
        if session.current_state is None:
            raise ValueError("An initial AcousticBrain state is required.")
        if session.pending_iteration is not None:
            raise ValueError("The current iteration must be completed first.")
        known_hypotheses = {
            item.code for item in session.current_state.hypotheses
        }
        if protocol.hypothesis_code not in known_hypotheses:
            raise ValueError("The experiment must reference a current hypothesis.")
        iteration = OptimizationIteration(
            number=len(session.iterations) + 1,
            protocol=protocol,
            before_state_id=session.current_state.state_id,
        )
        session.iterations.append(iteration)
        self._refresh_analysis(session)
        return iteration

    def attach_analysis(
        self,
        context: OptimizationSessionContext,
        analysis_context,
    ) -> AcousticBrainState:
        session = self._require_context(context)
        if session.states and session.pending_iteration is None:
            raise ValueError(
                "A new state requires an explicitly started iteration."
            )
        state = self._snapshot(
            session,
            analysis_context,
            len(session.states) + 1,
        )
        session.states.append(state)
        iteration = session.pending_iteration
        if iteration is not None:
            before = self._state(session, iteration.before_state_id)
            comparison = self._compare(
                session,
                iteration,
                before,
                state,
            )
            iteration.after_state_id = state.state_id
            iteration.comparison = comparison
        self._refresh_analysis(session)
        analysis_context.optimization_session_analysis = session.analysis
        return state

    @staticmethod
    def _require_context(context) -> OptimizationSession:
        if not isinstance(context, OptimizationSessionContext):
            raise TypeError("An explicit OptimizationSessionContext is required.")
        return context.session

    @staticmethod
    def _state(session, state_id):
        return next(item for item in session.states if item.state_id == state_id)

    @staticmethod
    def _snapshot(session, context, index):
        return OptimizationSessionService.snapshot_analysis(
            context,
            state_id=f"{session.session_id}:state:{index}",
        )

    @staticmethod
    def snapshot_analysis(context, *, state_id):
        """Crée un état PR-025 sans créer ni muter de session métier."""
        global_analysis = context.global_analysis
        reasoning = context.acoustic_reasoning_analysis
        traceability = context.traceability_analysis
        if global_analysis is None or reasoning is None or traceability is None:
            raise ValueError("A complete structured AcousticBrain state is required.")

        facts = []
        known_fact_codes = set()
        for evidence in traceability.evidence_references:
            if evidence.fact_code in known_fact_codes:
                continue
            facts.append(
                SessionFact(
                    code=evidence.fact_code,
                    source_analysis=evidence.source_analysis,
                    value=evidence.value,
                )
            )
            known_fact_codes.add(evidence.fact_code)
        for domain in global_analysis.domains:
            code = f"global.domain.{domain.code.lower()}.score"
            facts.append(
                SessionFact(
                    code=code,
                    source_analysis=domain.source_analysis,
                    value=domain.score,
                    higher_is_better=True,
                )
            )

        correlations = tuple(
            SessionCorrelation(
                code=item.code,
                fact_codes=tuple(
                    dict.fromkeys(
                        fact
                        for link in traceability.links
                        if item.code in link.correlation_codes
                        for fact in link.fact_codes
                    )
                ),
            )
            for item in global_analysis.correlations
        )
        hypotheses = tuple(
            SessionHypothesis(
                code=item.code.value,
                status=item.status.value,
                support_score=item.support_score,
                fact_codes=tuple(
                    dict.fromkeys(
                        evidence.fact_code
                        for collection in (
                            item.supporting_evidence,
                            item.counter_evidence,
                            item.context_evidence,
                        )
                        for evidence in collection
                    )
                ),
                correlation_codes=tuple(
                    dict.fromkeys(
                        code
                        for collection in (
                            item.supporting_evidence,
                            item.counter_evidence,
                            item.context_evidence,
                        )
                        for evidence in collection
                        for code in evidence.correlation_codes
                    )
                ),
            )
            for item in reasoning.hypotheses
        )
        return AcousticBrainState(
            state_id=state_id,
            measurement_name=context.measurement.name,
            global_score=global_analysis.score,
            facts=tuple(facts),
            correlations=correlations,
            hypotheses=hypotheses,
        )

    def _compare(self, session, iteration, before, after):
        improved, degraded = self._fact_changes(before, after)
        evolution = self._hypothesis_evolution(
            iteration.protocol.hypothesis_code,
            before,
            after,
        )
        return ExperimentComparison(
            comparison_id=(
                f"{session.session_id}:comparison:{iteration.number}"
            ),
            before_state_id=before.state_id,
            after_state_id=after.state_id,
            global_gain=(
                after.global_score - before.global_score
                if self._numeric(before.global_score, after.global_score)
                else None
            ),
            improved_facts=improved,
            degraded_facts=degraded,
            hypothesis_evolution=evolution,
        )

    @classmethod
    def _fact_changes(cls, before, after):
        before_facts = {item.code: item for item in before.facts}
        after_facts = {item.code: item for item in after.facts}
        improved = []
        degraded = []
        for code in sorted(before_facts.keys() & after_facts.keys()):
            old = before_facts[code]
            new = after_facts[code]
            if old.higher_is_better is None or not cls._numeric(old.value, new.value):
                continue
            if new.value == old.value:
                continue
            change = FactEvolution(code, old.value, new.value)
            is_improved = (new.value > old.value) == old.higher_is_better
            (improved if is_improved else degraded).append(change)
        return tuple(improved), tuple(degraded)

    @staticmethod
    def _numeric(*values):
        return all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in values
        )

    @staticmethod
    def _hypothesis_evolution(code, before, after):
        return OptimizationSessionService.compare_hypothesis(code, before, after)

    @staticmethod
    def compare_hypothesis(code, before, after):
        """Projette l'évolution PR-025 entre deux snapshots explicites."""
        old = next((item for item in before.hypotheses if item.code == code), None)
        new = next((item for item in after.hypotheses if item.code == code), None)
        old_status = old.status if old else None
        new_status = new.status if new else None
        old_score = old.support_score if old else None
        new_score = new.support_score if new else None
        status_rank = {
            "CONTRADICTED": -1,
            "INCONCLUSIVE": 0,
            "PLAUSIBLE": 1,
            "SUPPORTED": 2,
        }
        if new_status == "CONTRADICTED":
            result = HypothesisEvolutionResult.REFUTED
        elif status_rank.get(new_status, 0) > status_rank.get(old_status, 0):
            result = HypothesisEvolutionResult.REINFORCED
        elif status_rank.get(new_status, 0) < status_rank.get(old_status, 0):
            result = HypothesisEvolutionResult.WEAKENED
        elif old_score is not None and new_score is not None and new_score > old_score:
            result = HypothesisEvolutionResult.REINFORCED
        elif old_score is not None and new_score is not None and new_score < old_score:
            result = HypothesisEvolutionResult.WEAKENED
        else:
            result = HypothesisEvolutionResult.UNCHANGED
        return HypothesisEvolution(
            hypothesis_code=code,
            before_status=old_status,
            after_status=new_status,
            before_support_score=old_score,
            after_support_score=new_score,
            result=result,
        )

    @staticmethod
    def _refresh_analysis(session):
        completed = [item for item in session.iterations if item.is_completed]
        evolutions = [item.comparison.hypothesis_evolution for item in completed]
        latest = session.current_state
        open_hypotheses = tuple(
            item.code
            for item in (latest.hypotheses if latest else ())
            if item.status != "CONTRADICTED"
        )
        trace_chains = tuple(
            SessionTraceChain(
                source_state_id=item.before_state_id,
                measurement_name=OptimizationSessionService._state(
                    session, item.before_state_id
                ).measurement_name,
                fact_codes=OptimizationSessionService._trace_facts(item, session),
                correlation_codes=OptimizationSessionService._trace_correlations(
                    item, session
                ),
                hypothesis_code=item.protocol.hypothesis_code,
                protocol_id=item.protocol.experiment_id,
                new_state_id=item.after_state_id,
                comparison_id=item.comparison.comparison_id,
                evolution_result=item.comparison.hypothesis_evolution.result.value,
                progression_id=f"{session.session_id}:progression:{item.number}",
            )
            for item in completed
        )
        initial = session.states[0] if session.states else None
        global_gain = (
            latest.global_score - initial.global_score
            if initial
            and latest
            and OptimizationSessionService._numeric(
                initial.global_score, latest.global_score
            )
            else None
        )
        if initial is not None and latest is not None:
            improvements, degradations = (
                OptimizationSessionService._fact_changes(initial, latest)
            )
        else:
            improvements, degradations = (), ()
        pending = session.pending_iteration
        session.analysis = OptimizationSessionAnalysis(
            session_id=session.session_id,
            current_iteration=(pending.number if pending else len(completed)),
            completed_experiments=len(completed),
            open_hypotheses=open_hypotheses,
            reinforced_hypotheses=tuple(
                item.hypothesis_code
                for item in evolutions
                if item.result is HypothesisEvolutionResult.REINFORCED
            ),
            refuted_hypotheses=tuple(
                item.hypothesis_code
                for item in evolutions
                if item.result is HypothesisEvolutionResult.REFUTED
            ),
            global_gain=global_gain,
            main_improvements=tuple(item.fact_code for item in improvements),
            main_degradations=tuple(item.fact_code for item in degradations),
            pending_experiment=pending.protocol.label if pending else None,
            trace_chains=trace_chains,
        )

    @staticmethod
    def _trace_facts(iteration, session):
        state = OptimizationSessionService._state(session, iteration.before_state_id)
        hypothesis = next(
            item
            for item in state.hypotheses
            if item.code == iteration.protocol.hypothesis_code
        )
        return tuple(
            dict.fromkeys((*hypothesis.fact_codes, *iteration.protocol.fact_codes))
        )

    @staticmethod
    def _trace_correlations(iteration, session):
        state = OptimizationSessionService._state(session, iteration.before_state_id)
        hypothesis = next(
            item
            for item in state.hypotheses
            if item.code == iteration.protocol.hypothesis_code
        )
        return hypothesis.correlation_codes
