from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedCausalProtocolStep:
    step_index: int
    step_code: str
    experiment_id: str
    controlled_variable_codes: tuple[str, ...]
    changed_variable_codes: tuple[str, ...]
    unknown_variable_codes: tuple[str, ...]
    observation_codes: tuple[str, ...]


@dataclass(frozen=True)
class PresentedCausalTrajectory:
    trajectory_code: str
    support_score: float
    supporting_observation_codes: tuple[str, ...]
    counter_evidence_codes: tuple[str, ...]
    remaining_ambiguity_codes: tuple[str, ...]


@dataclass(frozen=True)
class PresentedCausalDiscrimination:
    protocol_code: str
    status: str
    completed_steps: tuple[PresentedCausalProtocolStep, ...]
    remaining_step_codes: tuple[str, ...]
    compatible_trajectories: tuple[PresentedCausalTrajectory, ...]
    contradicted_trajectories: tuple[PresentedCausalTrajectory, ...]
    resolved_discrimination_codes: tuple[str, ...]
    remaining_discrimination_codes: tuple[str, ...]
    new_ambiguity_codes: tuple[str, ...]
    lost_ambiguity_codes: tuple[str, ...]
    recommended_next_protocol: str | None
    trace_id: str
    trace_observation_codes: tuple[str, ...]
    trace_applied_rule_codes: tuple[str, ...]
    detailed_traceability: bool

    def to_dict(self):
        return asdict(self)


class CausalDiscriminationPresenter:
    """Projette le résultat causal sans produire de règle ni de trajectoire."""

    def present(self, context):
        analysis = getattr(context, "causal_discrimination_analysis", None)
        if analysis is None:
            return None
        trajectories = tuple(self._trajectory(item) for item in analysis.trajectory_assessments)
        return PresentedCausalDiscrimination(
            protocol_code=analysis.protocol_code,
            status=analysis.status.value,
            completed_steps=tuple(
                PresentedCausalProtocolStep(
                    step_index=item.step_index,
                    step_code=item.step_code,
                    experiment_id=item.experiment_id,
                    controlled_variable_codes=item.controlled_variable_codes,
                    changed_variable_codes=item.changed_variable_codes,
                    unknown_variable_codes=item.unknown_variable_codes,
                    observation_codes=item.observation_codes,
                )
                for item in analysis.completed_steps
            ),
            remaining_step_codes=analysis.remaining_step_codes,
            compatible_trajectories=tuple(
                item for source, item in zip(analysis.trajectory_assessments, trajectories)
                if source.status.value == "COMPATIBLE"
            ),
            contradicted_trajectories=tuple(
                item for source, item in zip(analysis.trajectory_assessments, trajectories)
                if source.status.value == "CONTRADICTED"
            ),
            resolved_discrimination_codes=analysis.resolved_discrimination_codes,
            remaining_discrimination_codes=analysis.remaining_discrimination_codes,
            new_ambiguity_codes=analysis.new_ambiguity_codes,
            lost_ambiguity_codes=analysis.lost_ambiguity_codes,
            recommended_next_protocol=analysis.recommended_next_protocol,
            trace_id=analysis.trace.trace_id,
            trace_observation_codes=analysis.trace.observation_codes,
            trace_applied_rule_codes=analysis.trace.applied_rule_codes,
            detailed_traceability=analysis.detailed_traceability,
        )

    @staticmethod
    def _trajectory(item):
        return PresentedCausalTrajectory(
            trajectory_code=item.trajectory_code.value,
            support_score=item.support_score,
            supporting_observation_codes=item.supporting_observation_codes,
            counter_evidence_codes=item.counter_evidence_codes,
            remaining_ambiguity_codes=item.remaining_ambiguity_codes,
        )
