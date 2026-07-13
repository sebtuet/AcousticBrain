from dataclasses import asdict, dataclass

from acousticbrain.models import ExperimentFactChange


@dataclass(frozen=True)
class PresentedExperimentEvolution:
    before_experiment_id: str
    after_experiment_id: str
    comparison_type: str
    eligibility: str
    ineligibility_reasons: tuple[str, ...]
    source_protocol_id: str | None
    source_hypothesis_code: str | None
    outcome: str
    improved_fact_codes: tuple[str, ...]
    degraded_fact_codes: tuple[str, ...]
    changed_fact_codes: tuple[str, ...]
    unchanged_fact_codes: tuple[str, ...]
    unavailable_fact_codes: tuple[str, ...]
    observation_labels: tuple[str, ...]
    counter_fact_codes: tuple[str, ...]
    unresolved_discrimination_labels: tuple[str, ...]
    technical_confidence: float | None
    trace_id: str
    trace_before_file_hash: str
    trace_after_file_hash: str
    trace_before_fact_codes: tuple[str, ...]
    trace_after_fact_codes: tuple[str, ...]
    trace_delta_fact_codes: tuple[str, ...]
    trace_observed_fact_codes: tuple[str, ...]
    trace_unresolved_discrimination_codes: tuple[str, ...]


@dataclass(frozen=True)
class PresentedExperimentComparison:
    chronology: tuple[str, ...]
    local_comparisons: tuple[PresentedExperimentEvolution, ...]
    cumulative_comparisons: tuple[PresentedExperimentEvolution, ...]
    detailed_traceability: bool

    def to_dict(self):
        return asdict(self)


class ExperimentComparisonPresenter:
    """Projection pure : les libellés sont une traduction fixe de codes calculés."""

    FACT_LABELS = {
        "SPATIAL_ASYMMETRY_DECREASED": "l’asymétrie spatiale diminue",
        "DRR_ASYMMETRY_DECREASED": "l’asymétrie directe/réverbérée diminue",
        "BASS_DECAY_ASYMMETRY_DECREASED": "l’asymétrie de décroissance grave diminue",
        "BASS_DECAY_REDUCED_AT_TARGET_BANDS": "la décroissance diminue dans les bandes ciblées",
        "BASS_DECAY_STABLE_AT_TARGET_BANDS": "la décroissance reste stable dans les bandes ciblées",
        "UNMATCHED_EVENT_COUNT_DECREASED": "le nombre d’événements temporels non appariés diminue",
        "TARGET_NULL_FREQUENCY_SHIFTED": "la fréquence du creux ciblé se déplace",
        "TARGET_NULL_DEPTH_REDUCED": "la profondeur du creux ciblé diminue",
        "TARGET_NULL_UNCHANGED": "le creux ciblé reste inchangé",
        "LEFT_RIGHT_DIFFERENCE_REPRODUCIBLE": "l’écart gauche/droite est reproductible",
        "CHANNEL_SPECIFIC_PATTERN_STABLE": "le motif spécifique aux canaux reste stable",
        "CHANNEL_SPECIFIC_PATTERN_CHANGED": "le motif spécifique aux canaux a changé",
    }
    DISCRIMINATION_LABELS = {
        "LOUDSPEAKER_VS_ROOM_SIDE": "la mesure ne distingue pas encore l’enceinte du côté de la pièce",
        "LOUDSPEAKER_VS_SIGNAL_CHAIN": "la mesure ne distingue pas encore l’enceinte de la chaîne du canal",
        "SIGNAL_CHAIN_VS_ROOM_SIDE": "la chaîne du canal reste une alternative au côté de la pièce",
        "LOCAL_POSITION_EFFECT_VS_GLOBAL_MODE": "un effet local de position reste à distinguer d’un mode global",
        "SOURCE_EXCITATION_VS_LISTENER_POSITION": "l’excitation par la source reste à distinguer de la position d’écoute",
        "CANDIDATE_SURFACE_VS_OTHER_SURFACE": "la surface candidate reste à distinguer des autres surfaces",
        "REFLECTION_VS_MEASUREMENT_VARIABILITY": "la réflexion reste à distinguer de la variabilité de mesure",
        "SBIR_VS_ROOM_MODE": "l’interaction SBIR reste à distinguer d’un mode de pièce",
        "CANDIDATE_SURFACE_VS_OTHER_BOUNDARY": "la surface candidate reste à distinguer des autres limites",
    }

    def present(self, context):
        analysis = getattr(context, "experiment_comparison_analysis", None)
        if analysis is None:
            return None
        return PresentedExperimentComparison(
            chronology=analysis.sequence.chronology,
            local_comparisons=tuple(
                self._comparison(item) for item in analysis.sequence.local_comparisons
            ),
            cumulative_comparisons=tuple(
                self._comparison(item) for item in analysis.sequence.cumulative_comparisons
            ),
            detailed_traceability=analysis.detailed_traceability,
        )

    def _comparison(self, item):
        changes = {change.value: tuple(
            delta.fact_code for delta in item.fact_deltas if delta.change.value == change.value
        ) for change in ExperimentFactChange}
        return PresentedExperimentEvolution(
            before_experiment_id=item.before_experiment_id,
            after_experiment_id=item.after_experiment_id,
            comparison_type=item.comparison_type.value,
            eligibility=item.eligibility.value,
            ineligibility_reasons=tuple(reason.value for reason in item.ineligibility_reasons),
            source_protocol_id=item.source_protocol_id,
            source_hypothesis_code=item.source_hypothesis_code,
            outcome=item.outcome.value,
            improved_fact_codes=changes["IMPROVED"],
            degraded_fact_codes=changes["DEGRADED"],
            changed_fact_codes=changes["CHANGED"],
            unchanged_fact_codes=changes["UNCHANGED"],
            unavailable_fact_codes=item.unavailable_fact_codes,
            observation_labels=tuple(
                self.FACT_LABELS.get(fact.code, fact.code) for fact in item.observed_facts
            ),
            counter_fact_codes=tuple(fact.code for fact in item.counter_facts),
            unresolved_discrimination_labels=tuple(
                self.DISCRIMINATION_LABELS.get(value.code, value.code)
                for value in item.unresolved_discriminations
            ),
            technical_confidence=item.technical_confidence,
            trace_id=item.trace.trace_id,
            trace_before_file_hash=item.trace.before_file_hash,
            trace_after_file_hash=item.trace.after_file_hash,
            trace_before_fact_codes=item.trace.before_fact_codes,
            trace_after_fact_codes=item.trace.after_fact_codes,
            trace_delta_fact_codes=item.trace.delta_fact_codes,
            trace_observed_fact_codes=item.trace.observed_fact_codes,
            trace_unresolved_discrimination_codes=(
                item.trace.unresolved_discrimination_codes
            ),
        )
