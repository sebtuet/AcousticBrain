from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedLongitudinalExperimentalLearningState:
    state_id: str
    hypothesis_code: str
    protocol_codes: tuple[str, ...]
    experiment_codes: tuple[str, ...]
    used_experiment_codes: tuple[str, ...]
    comparable_experiment_codes: tuple[str, ...]
    excluded_experiment_codes: tuple[tuple[str, str], ...]
    supporting_observation_ids: tuple[str, ...]
    contradicting_observation_ids: tuple[str, ...]
    unchanged_observation_ids: tuple[str, ...]
    inconclusive_observation_ids: tuple[str, ...]
    resolved_ambiguities: tuple[str, ...]
    remaining_ambiguities: tuple[str, ...]
    deferred_discriminations: tuple[str, ...]
    learning_status: str
    next_information_need: str
    causality_status: str
    provenance: tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True)
class PresentedLongitudinalExperimentalLearningAnalysis:
    states: tuple[PresentedLongitudinalExperimentalLearningState, ...]
    applied_rule_codes: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


class LongitudinalExperimentalLearningPresenter:
    """Traduit l'état dérivé sans ajouter de conclusion."""

    def present(self, context):
        analysis = getattr(
            context, "longitudinal_experimental_learning_analysis", None
        )
        if analysis is None:
            return None
        return PresentedLongitudinalExperimentalLearningAnalysis(
            states=tuple(self._state(item) for item in analysis.states),
            applied_rule_codes=analysis.applied_rule_codes,
        )

    @staticmethod
    def _state(item):
        excluded = tuple(sorted((
            *((code, "NOT_COMPARABLE") for code in item.non_comparable_experiment_codes),
            *((code, "UNKNOWN_DECLARATION") for code in item.unknown_declaration_codes),
        )))
        return PresentedLongitudinalExperimentalLearningState(
            state_id=item.state_id,
            hypothesis_code=item.hypothesis_code,
            protocol_codes=item.protocol_codes,
            experiment_codes=item.experiment_codes,
            used_experiment_codes=tuple(sorted(
                set(item.comparable_experiment_codes)
                & (
                    set(item.controlled_intervention_codes)
                    | set(item.measurement_repeat_codes)
                )
            )),
            comparable_experiment_codes=item.comparable_experiment_codes,
            excluded_experiment_codes=excluded,
            supporting_observation_ids=item.supporting_observation_ids,
            contradicting_observation_ids=item.contradicting_observation_ids,
            unchanged_observation_ids=item.unchanged_observation_ids,
            inconclusive_observation_ids=item.inconclusive_observation_ids,
            resolved_ambiguities=item.resolved_ambiguities,
            remaining_ambiguities=item.remaining_ambiguities,
            deferred_discriminations=item.deferred_discriminations,
            learning_status=item.learning_status.value,
            next_information_need=item.next_information_need,
            causality_status=item.causality_status,
            provenance=item.provenance,
        )
