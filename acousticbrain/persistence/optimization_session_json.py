import json
from dataclasses import asdict
from pathlib import Path

from acousticbrain.models import (
    AcousticBrainState,
    ExperimentComparison,
    ExperimentProtocol,
    FactEvolution,
    HypothesisEvolution,
    HypothesisEvolutionResult,
    OptimizationIteration,
    OptimizationSession,
    SessionCorrelation,
    SessionFact,
    SessionHypothesis,
)


class OptimizationSessionJsonRepository:
    """Persistance JSON explicite et versionnée des seules données de session."""

    SCHEMA_VERSION = 1

    def save(self, session: OptimizationSession, path) -> None:
        if not isinstance(session, OptimizationSession):
            raise TypeError("OptimizationSession is required.")
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "optimization_session": {
                "session_id": session.session_id,
                "detailed_traceability": session.detailed_traceability,
                "states": [asdict(item) for item in session.states],
                "iterations": [self._iteration_to_dict(item) for item in session.iterations],
            },
        }
        Path(path).write_text(
            json.dumps(payload, indent=2, sort_keys=True, allow_nan=False),
            encoding="utf-8",
        )

    def load(self, path) -> OptimizationSession:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError("Unsupported optimization-session schema version.")
        raw = payload.get("optimization_session")
        if not isinstance(raw, dict):
            raise ValueError("Invalid optimization-session document.")
        session = OptimizationSession(
            session_id=raw["session_id"],
            detailed_traceability=bool(raw.get("detailed_traceability", False)),
            states=[self._state(item) for item in raw.get("states", [])],
            iterations=[self._iteration(item) for item in raw.get("iterations", [])],
        )
        self._validate_references(session)
        return session

    @staticmethod
    def _iteration_to_dict(iteration):
        data = asdict(iteration)
        if iteration.comparison is not None:
            data["comparison"]["hypothesis_evolution"]["result"] = (
                iteration.comparison.hypothesis_evolution.result.value
            )
        return data

    @staticmethod
    def _state(raw):
        return AcousticBrainState(
            state_id=raw["state_id"],
            measurement_name=raw["measurement_name"],
            global_score=raw.get("global_score"),
            facts=tuple(SessionFact(**item) for item in raw.get("facts", [])),
            correlations=tuple(
                SessionCorrelation(
                    code=item["code"],
                    fact_codes=tuple(item.get("fact_codes", [])),
                )
                for item in raw.get("correlations", [])
            ),
            hypotheses=tuple(
                SessionHypothesis(
                    code=item["code"],
                    status=item["status"],
                    support_score=item["support_score"],
                    fact_codes=tuple(item.get("fact_codes", [])),
                    correlation_codes=tuple(item.get("correlation_codes", [])),
                )
                for item in raw.get("hypotheses", [])
            ),
        )

    @classmethod
    def _iteration(cls, raw):
        protocol_raw = raw["protocol"]
        protocol = ExperimentProtocol(
            experiment_id=protocol_raw["experiment_id"],
            hypothesis_code=protocol_raw["hypothesis_code"],
            action_code=protocol_raw["action_code"],
            label=protocol_raw["label"],
            fact_codes=tuple(protocol_raw.get("fact_codes", [])),
        )
        comparison = cls._comparison(raw.get("comparison"))
        return OptimizationIteration(
            number=raw["number"],
            protocol=protocol,
            before_state_id=raw["before_state_id"],
            after_state_id=raw.get("after_state_id"),
            comparison=comparison,
        )

    @staticmethod
    def _comparison(raw):
        if raw is None:
            return None
        evolution = raw["hypothesis_evolution"]
        return ExperimentComparison(
            comparison_id=raw["comparison_id"],
            before_state_id=raw["before_state_id"],
            after_state_id=raw["after_state_id"],
            global_gain=raw.get("global_gain"),
            improved_facts=tuple(
                FactEvolution(**item) for item in raw.get("improved_facts", [])
            ),
            degraded_facts=tuple(
                FactEvolution(**item) for item in raw.get("degraded_facts", [])
            ),
            hypothesis_evolution=HypothesisEvolution(
                hypothesis_code=evolution["hypothesis_code"],
                before_status=evolution.get("before_status"),
                after_status=evolution.get("after_status"),
                before_support_score=evolution.get("before_support_score"),
                after_support_score=evolution.get("after_support_score"),
                result=HypothesisEvolutionResult(evolution["result"]),
            ),
        )

    @staticmethod
    def _validate_references(session):
        state_ids = {item.state_id for item in session.states}
        if len(state_ids) != len(session.states):
            raise ValueError("Session state ids must be unique.")
        for iteration in session.iterations:
            if iteration.before_state_id not in state_ids:
                raise ValueError("Iteration before-state reference is invalid.")
            if iteration.after_state_id and iteration.after_state_id not in state_ids:
                raise ValueError("Iteration after-state reference is invalid.")
