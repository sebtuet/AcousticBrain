from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedHistoricalExperiment:
    experiment_code: str
    declaration_status: str


@dataclass(frozen=True)
class PresentedResolvedAmbiguityProvenance:
    ambiguity_code: str
    source_analysis_code: str
    source_id: str
    protocol_code: str
    source_experiments: tuple[PresentedHistoricalExperiment, ...]


@dataclass(frozen=True)
class PresentedLongitudinalExperimentalLearningState:
    state_id: str
    hypothesis_code: str
    protocol_codes: tuple[str, ...]
    historical_context_experiments: tuple[PresentedHistoricalExperiment, ...]
    evidence_contributing_experiment_codes: tuple[str, ...]
    campaign_source_experiments: tuple[PresentedHistoricalExperiment, ...]
    discrimination_source_experiments: tuple[PresentedHistoricalExperiment, ...]
    comparable_experiment_codes: tuple[str, ...]
    excluded_experiments: tuple[tuple[str, str], ...]
    supporting_observation_ids: tuple[str, ...]
    contradicting_observation_ids: tuple[str, ...]
    unchanged_observation_ids: tuple[str, ...]
    inconclusive_observation_ids: tuple[str, ...]
    resolved_ambiguities: tuple[str, ...]
    resolved_ambiguity_provenance: tuple[
        PresentedResolvedAmbiguityProvenance, ...
    ]
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
        statuses = dict(item.historical_experiment_declaration_statuses)
        excluded_reasons = {}
        for code in item.non_comparable_experiment_codes:
            excluded_reasons.setdefault(code, []).append("NOT_COMPARABLE")
        for code in item.unknown_declaration_codes:
            excluded_reasons.setdefault(code, []).append("UNKNOWN_DECLARATION")
        excluded = tuple(
            (code, "+".join(sorted(reasons)))
            for code, reasons in sorted(excluded_reasons.items())
        )

        def experiments(codes):
            return tuple(
                PresentedHistoricalExperiment(
                    experiment_code=code,
                    declaration_status=statuses.get(
                        code,
                        "DECLARATION_UNAVAILABLE",
                    ),
                )
                for code in codes
            )

        return PresentedLongitudinalExperimentalLearningState(
            state_id=item.state_id,
            hypothesis_code=item.hypothesis_code,
            protocol_codes=item.protocol_codes,
            historical_context_experiments=experiments(
                item.historical_context_experiment_codes
            ),
            evidence_contributing_experiment_codes=(
                item.evidence_contributing_experiment_codes
            ),
            campaign_source_experiments=experiments(
                item.campaign_source_experiment_codes
            ),
            discrimination_source_experiments=experiments(
                item.discrimination_source_experiment_codes
            ),
            comparable_experiment_codes=item.comparable_experiment_codes,
            excluded_experiments=excluded,
            supporting_observation_ids=item.supporting_observation_ids,
            contradicting_observation_ids=item.contradicting_observation_ids,
            unchanged_observation_ids=item.unchanged_observation_ids,
            inconclusive_observation_ids=item.inconclusive_observation_ids,
            resolved_ambiguities=item.resolved_ambiguities,
            resolved_ambiguity_provenance=tuple(
                PresentedResolvedAmbiguityProvenance(
                    ambiguity_code=source.ambiguity_code,
                    source_analysis_code=source.source_analysis_code,
                    source_id=source.source_id,
                    protocol_code=source.protocol_code,
                    source_experiments=experiments(
                        source.source_experiment_codes
                    ),
                )
                for source in item.resolved_ambiguity_provenance
            ),
            remaining_ambiguities=item.remaining_ambiguities,
            deferred_discriminations=item.deferred_discriminations,
            learning_status=item.learning_status.value,
            next_information_need=item.next_information_need,
            causality_status=item.causality_status,
            provenance=item.provenance,
        )
