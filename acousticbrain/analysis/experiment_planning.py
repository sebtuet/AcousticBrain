from dataclasses import dataclass, replace
from statistics import fmean

from acousticbrain.models import (
    CausalDiscriminationOutcome,
    ExperimentCandidate,
    ExperimentCostCategory,
    ExperimentDifficulty,
    ExperimentPlan,
    ExperimentPlanningAnalysis,
    ExperimentPlanningStatus,
    ExperimentPlanningTraceLink,
    ExperimentReversibility,
    ExperimentSelectionReason,
    HypothesisCode,
    HypothesisStatus,
)


@dataclass(frozen=True)
class _ProtocolDefinition:
    protocol_id: str
    hypothesis_code: HypothesisCode
    action_code: str
    objective_code: str
    difficulty: ExperimentDifficulty
    duration_minutes: int | None
    cost: ExperimentCostCategory
    reversibility: ExperimentReversibility
    observable_fact_codes: tuple[str, ...]
    discriminated_hypothesis_codes: tuple[HypothesisCode, ...]
    prerequisite_parameters: tuple[str, ...] = ()
    geometry_parameters: tuple[str, ...] = ()
    controlled_variable_codes: tuple[str, ...] = ()
    changed_variable_codes: tuple[str, ...] = ()


class ExperimentPlanner:
    """Classe des protocoles sans exécuter ni modifier le système analysé."""

    MAXIMUM_GEOMETRY_TIMING_ERROR_MS = 1.0
    MAXIMUM_GEOMETRY_UNCERTAINTY_MS = 0.5
    MINIMUM_GEOMETRY_CONFIDENCE = 70.0
    MAXIMUM_SBIR_FREQUENCY_ERROR_PERCENT = 15.0
    MAXIMUM_SBIR_PREDICTION_UNCERTAINTY_PERCENT = 10.0

    RULE_CODES = (
        "PLAN_REQUIRE_STRUCTURED_SOURCE",
        "PLAN_REQUIRE_OBSERVABLE_FACTS",
        "PLAN_EXCLUDE_COMPLETED",
        "PLAN_EXCLUDE_CONTRADICTED",
        "PLAN_EXCLUDE_USER_DEFERRED",
        "PLAN_EXCLUDE_COMPLETED_CAUSAL_DISCRIMINATION",
        "PLAN_REQUIRE_EXECUTABLE_ACQUISITION_PROTOCOL",
        "PLAN_REQUIRE_REVERSIBLE",
        "PLAN_INFORMATION_VALUE_V1",
        "PLAN_DETERMINISTIC_ORDER_V1",
    )

    PROTOCOLS = (
        _ProtocolDefinition(
            protocol_id="protocol.verify_speaker_room_asymmetry.v1",
            hypothesis_code=HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
            action_code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
            objective_code="DISCRIMINATE_CHANNEL_AND_ROOM_ASYMMETRY",
            difficulty=ExperimentDifficulty.EASY,
            duration_minutes=15,
            cost=ExperimentCostCategory.LOW,
            reversibility=ExperimentReversibility.HIGH,
            observable_fact_codes=(
                "stereo.symmetry_score",
                "spatial.pair_analysis",
                "etc.channel_specific_event_difference",
                "verification.asymmetry_persists_by_channel",
                "verification.asymmetry_disappears_after_control",
            ),
            discriminated_hypothesis_codes=(
                HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
                HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION,
            ),
        ),
        _ProtocolDefinition(
            protocol_id="protocol.verify_modal_bass_persistence.v1",
            hypothesis_code=HypothesisCode.MODAL_BASS_PERSISTENCE,
            action_code="VERIFY_MODAL_BASS_PERSISTENCE",
            objective_code="DISCRIMINATE_LOCAL_AND_GLOBAL_BASS_DECAY",
            difficulty=ExperimentDifficulty.MEDIUM,
            duration_minutes=45,
            cost=ExperimentCostCategory.LOW,
            reversibility=ExperimentReversibility.HIGH,
            observable_fact_codes=(
                "bass_decay.maximum_decay_time",
                "bass_decay.correlation.SLOW_DECAY_MODAL_INTERACTION",
                "verification.decay_frequency_shifts_by_position",
                "verification.decay_is_position_independent",
            ),
            discriminated_hypothesis_codes=(
                HypothesisCode.MODAL_BASS_PERSISTENCE,
                HypothesisCode.SBIR_PLACEMENT_INTERACTION,
            ),
        ),
        _ProtocolDefinition(
            protocol_id="protocol.temporary_mask_surface.v1",
            hypothesis_code=HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION,
            action_code="VERIFY_DOMINANT_EARLY_REFLECTION",
            objective_code="DISCRIMINATE_CANDIDATE_EARLY_REFLECTION_SURFACE",
            difficulty=ExperimentDifficulty.MEDIUM,
            duration_minutes=30,
            cost=ExperimentCostCategory.LOW,
            reversibility=ExperimentReversibility.HIGH,
            observable_fact_codes=(
                "etc.available_channels",
                "etc_reflection.geometry_surface_match",
                "geometry_early_reflection.theoretical_delay_ms",
                "etc_reflection.geometry_timing_error_ms",
                "REFLECTION_DECREASES_AFTER_MASKING",
                "REFLECTION_REMAINS_UNCHANGED_AFTER_MASKING",
            ),
            discriminated_hypothesis_codes=(
                HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION,
                HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
            ),
            prerequisite_parameters=(
                "surface",
                "observed_channel",
                "observed_event_delay_ms",
                "observed_event_relative_level_db",
                "theoretical_delay_ms",
                "timing_error_ms",
                "geometry_uncertainty_ms",
                "geometry_confidence",
                "geometry_path_id",
            ),
            geometry_parameters=(
                "surface",
                "theoretical_delay_ms",
                "timing_error_ms",
                "geometry_uncertainty_ms",
                "geometry_confidence",
                "geometry_path_id",
            ),
            controlled_variable_codes=(
                "MICROPHONE_POSITION",
                "LOUDSPEAKER_POSITION",
                "LOUDSPEAKER_ORIENTATION",
                "SIGNAL_CHAIN_ASSIGNMENT",
                "MEASUREMENT_LEVEL",
                "ROOM_CONFIGURATION",
            ),
            changed_variable_codes=("SURFACE_MASKING_STATE",),
        ),
        _ProtocolDefinition(
            protocol_id="protocol.temporary_move_speaker.v1",
            hypothesis_code=HypothesisCode.SBIR_PLACEMENT_INTERACTION,
            action_code="VERIFY_SBIR_PLACEMENT",
            objective_code="DISCRIMINATE_SBIR_PLACEMENT_INTERACTION",
            difficulty=ExperimentDifficulty.MEDIUM,
            duration_minutes=30,
            cost=ExperimentCostCategory.LOW,
            reversibility=ExperimentReversibility.HIGH,
            observable_fact_codes=(
                "sbir.geometry_frequency_match",
                "sbir.geometry_surface_id",
                "sbir.predicted_cancellation_frequency_hz",
                "sbir.geometry_frequency_error_percent",
                "SBIR_MOVES_WITH_SPEAKER",
                "SBIR_REMAINS_FIXED",
            ),
            discriminated_hypothesis_codes=(
                HypothesisCode.SBIR_PLACEMENT_INTERACTION,
                HypothesisCode.MODAL_BASS_PERSISTENCE,
            ),
            prerequisite_parameters=(
                "surface",
                "speaker_id",
                "listening_position_id",
                "geometry_candidate_id",
                "geometry_path_id",
                "measured_frequency_hz",
                "predicted_frequency_hz",
                "frequency_error_percent",
                "frequency_uncertainty_percent",
                "geometry_confidence",
                "current_distance_m",
                "proposed_displacement_m",
            ),
            geometry_parameters=(
                "surface",
                "speaker_id",
                "listening_position_id",
                "geometry_candidate_id",
                "geometry_path_id",
                "predicted_frequency_hz",
                "frequency_uncertainty_percent",
                "geometry_confidence",
                "current_distance_m",
            ),
            controlled_variable_codes=(
                "MICROPHONE_POSITION",
                "LOUDSPEAKER_ORIENTATION",
                "OTHER_LOUDSPEAKER_POSITIONS",
                "SIGNAL_CHAIN_ASSIGNMENT",
                "MEASUREMENT_LEVEL",
                "ROOM_CONFIGURATION",
            ),
            changed_variable_codes=("LOUDSPEAKER_POSITION",),
        ),
    )

    def plan(
        self,
        reasoning_analysis,
        *,
        session=None,
        deferred_action_codes=(),
        completed_protocol_ids=(),
        causal_discrimination_analysis=None,
        generated_experiment_analysis=None,
    ):
        hypotheses = {
            item.code: item for item in reasoning_analysis.hypotheses
        }
        candidates = tuple(
            self._apply_protocol_state(
                self._candidate(
                    definition,
                    hypotheses.get(definition.hypothesis_code),
                    session,
                ),
                definition,
                deferred_action_codes,
                completed_protocol_ids,
                causal_discrimination_analysis,
                generated_experiment_analysis,
            )
            for definition in self.PROTOCOLS
        )
        ordered_all = tuple(sorted(candidates, key=self._sort_key))
        eligible = tuple(item for item in ordered_all if item.eligible)
        ineligible = tuple(item for item in ordered_all if not item.eligible)
        recommended = eligible[0] if eligible else None
        source_analyses = tuple(
            dict.fromkeys(
                source
                for candidate in ordered_all
                for source in candidate.source_analysis_codes
            )
        )
        plan = ExperimentPlan(
            ordered_candidates=eligible,
            recommended_candidate=recommended,
            ineligible_candidates=ineligible,
            applied_rule_codes=self.RULE_CODES,
            technical_confidence=(
                fmean(item.confidence for item in eligible)
                if eligible
                else None
            ),
            source_analysis_codes=source_analyses,
        )
        ranks = {
            item.candidate_id: index
            for index, item in enumerate(eligible, start=1)
        }
        trace_links = tuple(
            ExperimentPlanningTraceLink(
                trace_id=f"planning.trace.{item.candidate_id}",
                fact_codes=item.observable_fact_codes,
                evidence_codes=tuple(
                    f"evidence.reasoning.{code.lower()}"
                    for code in item.evidence_codes
                ),
                hypothesis_code=item.hypothesis_code,
                source_protocol_id=item.source_protocol_id,
                candidate_id=item.candidate_id,
                rank=ranks.get(item.candidate_id),
                recommended=(
                    recommended is not None
                    and item.candidate_id == recommended.candidate_id
                ),
                session_iteration_number=self._session_iteration(
                    item, session
                ),
            )
            for item in ordered_all
        )
        return ExperimentPlanningAnalysis(
            status=(
                ExperimentPlanningStatus.READY
                if recommended is not None
                else ExperimentPlanningStatus.NO_ELIGIBLE_CANDIDATE
            ),
            plan=plan,
            trace_links=trace_links,
        )

    @staticmethod
    def _apply_protocol_state(
        candidate,
        definition,
        deferred_action_codes,
        completed_protocol_ids,
        causal_discrimination_analysis,
        generated_experiment_analysis,
    ):
        reasons = list(candidate.ineligibility_reasons)
        if definition.action_code in deferred_action_codes:
            reasons.append(ExperimentSelectionReason.USER_DEFERRED)
        if definition.protocol_id in completed_protocol_ids:
            reasons.append(ExperimentSelectionReason.ALREADY_COMPLETED)
        if (
            definition.action_code == "VERIFY_SPEAKER_ROOM_ASYMMETRY"
            and causal_discrimination_analysis is not None
            and getattr(causal_discrimination_analysis, "protocol_code", None)
            == "VERIFY_SPEAKER_ROOM_ASYMMETRY"
            and causal_discrimination_analysis.outcome
            is CausalDiscriminationOutcome.DISCRIMINATED
            and not causal_discrimination_analysis.remaining_discrimination_codes
            and causal_discrimination_analysis.recommended_next_protocol is None
        ):
            reasons.append(
                ExperimentSelectionReason.CAUSAL_DISCRIMINATION_COMPLETED
            )
        if (
            definition.action_code == "VERIFY_MODAL_BASS_PERSISTENCE"
            and not ExperimentPlanner._has_executable_generated_candidate(
                generated_experiment_analysis,
                definition.hypothesis_code.value,
            )
        ):
            reasons.append(
                ExperimentSelectionReason.ACQUISITION_PROTOCOL_INCOMPLETE
            )
        if not reasons:
            return candidate
        return replace(
            candidate,
            ineligibility_reasons=tuple(dict.fromkeys(reasons)),
            eligible=False,
        )

    @staticmethod
    def _has_executable_generated_candidate(analysis, hypothesis_code):
        return bool(
            analysis is not None
            and any(
                item.hypothesis_code == hypothesis_code and item.eligible
                for item in analysis.ordered_experiments
            )
        )

    def _candidate(self, definition, hypothesis, session):
        if hypothesis is None:
            return self._missing_hypothesis_candidate(definition)
        action = next(
            (
                item
                for item in hypothesis.verification_actions
                if item.code == definition.action_code
            ),
            None,
        )
        parameters = dict(action.parameters) if action is not None else {}
        evidence = tuple(
            item
            for collection in (
                hypothesis.supporting_evidence,
                hypothesis.counter_evidence,
                hypothesis.context_evidence,
            )
            for item in collection
        )
        source_analyses = tuple(
            dict.fromkeys(
                (
                    *(item.source_analysis for item in evidence),
                    *(item.source_analysis for item in hypothesis.missing_facts),
                )
            )
        )
        missing_codes = {item.fact_code for item in hypothesis.missing_facts}
        observable = tuple(
            dict.fromkeys(
                (
                    *definition.observable_fact_codes,
                    *(
                        action.expected_supporting_fact_codes
                        if action is not None
                        else ()
                    ),
                    *(
                        action.expected_counter_fact_codes
                        if action is not None
                        else ()
                    ),
                )
            )
        )
        unmet = tuple(
            name
            for name in definition.prerequisite_parameters
            if parameters.get(name) is None
        )
        ineligibility = []
        if not definition.protocol_id:
            ineligibility.append(
                ExperimentSelectionReason.SOURCE_PROTOCOL_MISSING
            )
        if not source_analyses:
            ineligibility.append(
                ExperimentSelectionReason.INCOMPLETE_PROVENANCE
            )
        if not observable:
            ineligibility.append(
                ExperimentSelectionReason.OBSERVABLE_FACTS_MISSING
            )
        if unmet:
            ineligibility.append(
                ExperimentSelectionReason.PREREQUISITE_MISSING
            )
        if any(name in definition.geometry_parameters for name in unmet):
            ineligibility.append(
                ExperimentSelectionReason.GEOMETRY_PARAMETER_MISSING
            )
        if definition.action_code == "VERIFY_DOMINANT_EARLY_REFLECTION":
            timing_error = parameters.get("timing_error_ms")
            uncertainty = parameters.get("geometry_uncertainty_ms")
            geometry_confidence = parameters.get("geometry_confidence")
            if (
                timing_error is not None
                and timing_error > self.MAXIMUM_GEOMETRY_TIMING_ERROR_MS
            ):
                ineligibility.append(
                    ExperimentSelectionReason.GEOMETRY_TIMING_INCOMPATIBLE
                )
            if (
                uncertainty is not None
                and uncertainty > self.MAXIMUM_GEOMETRY_UNCERTAINTY_MS
            ):
                ineligibility.append(
                    ExperimentSelectionReason.GEOMETRY_UNCERTAINTY_TOO_HIGH
                )
            if (
                geometry_confidence is not None
                and geometry_confidence < self.MINIMUM_GEOMETRY_CONFIDENCE
            ):
                ineligibility.append(
                    ExperimentSelectionReason.GEOMETRY_CONFIDENCE_TOO_LOW
                )
        if definition.action_code == "VERIFY_SBIR_PLACEMENT":
            frequency_error = parameters.get("frequency_error_percent")
            prediction_uncertainty = parameters.get(
                "frequency_uncertainty_percent"
            )
            geometry_confidence = parameters.get("geometry_confidence")
            if (
                frequency_error is not None
                and frequency_error
                > self.MAXIMUM_SBIR_FREQUENCY_ERROR_PERCENT
            ):
                ineligibility.append(
                    ExperimentSelectionReason.SBIR_FREQUENCY_MISMATCH_TOO_HIGH
                )
            if (
                prediction_uncertainty is not None
                and prediction_uncertainty
                > self.MAXIMUM_SBIR_PREDICTION_UNCERTAINTY_PERCENT
            ):
                ineligibility.append(
                    ExperimentSelectionReason.SBIR_PREDICTION_UNCERTAINTY_TOO_HIGH
                )
            if (
                geometry_confidence is not None
                and geometry_confidence < self.MINIMUM_GEOMETRY_CONFIDENCE
            ):
                ineligibility.append(
                    ExperimentSelectionReason.GEOMETRY_CONFIDENCE_TOO_LOW
                )
        if hypothesis.status is HypothesisStatus.CONTRADICTED:
            ineligibility.append(
                ExperimentSelectionReason.HYPOTHESIS_REFUTED
            )
        if definition.reversibility is ExperimentReversibility.NONE:
            ineligibility.append(ExperimentSelectionReason.NON_REVERSIBLE)
        candidate_id = (
            "experiment_candidate."
            f"{definition.hypothesis_code.value.lower()}"
        )
        already_completed = self._already_completed(
            candidate_id, definition, session
        )
        if already_completed:
            ineligibility.append(
                ExperimentSelectionReason.ALREADY_COMPLETED
            )

        resolved_missing = len(missing_codes.intersection(observable))
        informative_value = self.informative_value(
            support_score=hypothesis.support_score,
            confidence=hypothesis.confidence,
            missing_fact_count=len(missing_codes),
            resolved_missing_fact_count=resolved_missing,
            counter_evidence_count=len(hypothesis.counter_evidence),
            discriminated_hypothesis_count=len(
                definition.discriminated_hypothesis_codes
            ),
            reversibility=definition.reversibility,
            difficulty=definition.difficulty,
            duration_minutes=definition.duration_minutes,
            cost=definition.cost,
            repetition_count=1 if already_completed else 0,
        )
        return ExperimentCandidate(
            candidate_id=candidate_id,
            hypothesis_code=definition.hypothesis_code.value,
            source_action_code=action.code if action is not None else None,
            source_protocol_id=definition.protocol_id,
            hypothesis_status=hypothesis.status.value,
            support_score=hypothesis.support_score,
            confidence=hypothesis.confidence,
            counter_evidence_count=len(hypothesis.counter_evidence),
            missing_fact_count=len(hypothesis.missing_facts),
            informative_value=informative_value,
            difficulty=definition.difficulty,
            estimated_duration_minutes=definition.duration_minutes,
            cost_category=definition.cost,
            reversibility=definition.reversibility,
            objective_code=definition.objective_code,
            observable_fact_codes=observable,
            discriminated_hypothesis_codes=tuple(
                item.value
                for item in definition.discriminated_hypothesis_codes
            ),
            prerequisite_codes=definition.prerequisite_parameters,
            unmet_prerequisite_codes=unmet,
            selection_reasons=self._selection_reasons(
                hypothesis,
                resolved_missing,
                definition,
            ),
            ineligibility_reasons=tuple(dict.fromkeys(ineligibility)),
            source_analysis_codes=source_analyses,
            evidence_codes=tuple(item.code for item in evidence),
            applied_rule_codes=tuple(
                dict.fromkeys(
                    (
                        *hypothesis.applied_rule_codes,
                        *(item.rule_code for item in hypothesis.missing_facts),
                        "PLAN_INFORMATION_VALUE_V1",
                    )
                )
            ),
            eligible=not ineligibility,
            parameters=parameters,
            controlled_variable_codes=definition.controlled_variable_codes,
            changed_variable_codes=definition.changed_variable_codes,
        )

    @staticmethod
    def informative_value(
        *,
        support_score,
        confidence,
        missing_fact_count,
        resolved_missing_fact_count,
        counter_evidence_count,
        discriminated_hypothesis_count,
        reversibility,
        difficulty,
        duration_minutes,
        cost,
        repetition_count=0,
    ):
        uncertainty = 100.0 - abs(support_score - 50.0) * 2.0
        missing_resolution = (
            min(100.0, resolved_missing_fact_count / missing_fact_count * 100.0)
            if missing_fact_count
            else 0.0
        )
        counter_resolution = min(100.0, counter_evidence_count / 3.0 * 100.0)
        discrimination = min(
            100.0,
            max(0, discriminated_hypothesis_count - 1) / 3.0 * 100.0,
        )
        reversibility_score = {
            ExperimentReversibility.NONE: 0.0,
            ExperimentReversibility.LOW: 25.0,
            ExperimentReversibility.MEDIUM: 60.0,
            ExperimentReversibility.HIGH: 100.0,
        }[reversibility]
        difficulty_penalty = {
            ExperimentDifficulty.EASY: 0.0,
            ExperimentDifficulty.MEDIUM: 5.0,
            ExperimentDifficulty.HARD: 10.0,
        }[difficulty]
        cost_penalty = {
            ExperimentCostCategory.FREE: 0.0,
            ExperimentCostCategory.LOW: 2.0,
            ExperimentCostCategory.MEDIUM: 5.0,
            ExperimentCostCategory.HIGH: 10.0,
        }[cost]
        duration_penalty = 0.0
        if duration_minutes is not None:
            if duration_minutes > 60:
                duration_penalty = 8.0
            elif duration_minutes > 30:
                duration_penalty = 5.0
            elif duration_minutes > 15:
                duration_penalty = 2.0
        repetition_penalty = min(30.0, repetition_count * 20.0)
        value = (
            uncertainty * 0.25
            + support_score * 0.10
            + confidence * 0.10
            + missing_resolution * 0.20
            + counter_resolution * 0.10
            + discrimination * 0.10
            + reversibility_score * 0.10
            - difficulty_penalty
            - duration_penalty
            - cost_penalty
            - repetition_penalty
        )
        return round(min(100.0, max(0.0, value)), 2)

    @staticmethod
    def _selection_reasons(hypothesis, resolved_missing, definition):
        reasons = []
        uncertainty = 100.0 - abs(hypothesis.support_score - 50.0) * 2.0
        if uncertainty >= 60.0:
            reasons.append(ExperimentSelectionReason.HIGH_UNCERTAINTY)
        if resolved_missing:
            reasons.append(ExperimentSelectionReason.RESOLVES_MISSING_FACTS)
        if hypothesis.counter_evidence:
            reasons.append(
                ExperimentSelectionReason.DISCRIMINATES_COUNTER_EVIDENCE
            )
        if len(definition.discriminated_hypothesis_codes) > 1:
            reasons.append(
                ExperimentSelectionReason.DISCRIMINATES_HYPOTHESES
            )
        if definition.reversibility is ExperimentReversibility.HIGH:
            reasons.append(ExperimentSelectionReason.HIGH_REVERSIBILITY)
        if definition.difficulty is ExperimentDifficulty.EASY:
            reasons.append(ExperimentSelectionReason.LOW_DIFFICULTY)
        if definition.cost <= ExperimentCostCategory.LOW:
            reasons.append(ExperimentSelectionReason.LOW_COST)
        if hypothesis.confidence >= 70.0:
            reasons.append(ExperimentSelectionReason.HIGH_CONFIDENCE)
        return tuple(reasons)

    @staticmethod
    def _already_completed(candidate_id, definition, session):
        if session is None:
            return False
        return any(
            iteration.is_completed
            and (
                iteration.protocol.experiment_id == candidate_id
                or iteration.protocol.action_code == definition.action_code
            )
            for iteration in session.iterations
        )

    @staticmethod
    def _session_iteration(candidate, session):
        if session is None:
            return None
        iteration = session.pending_iteration
        if iteration is None:
            return None
        if (
            iteration.protocol.experiment_id == candidate.candidate_id
            or iteration.protocol.action_code == candidate.source_action_code
        ):
            return iteration.number
        return None

    @staticmethod
    def _sort_key(candidate):
        return (
            -candidate.informative_value,
            not candidate.eligible,
            -candidate.reversibility,
            candidate.difficulty,
            (
                candidate.estimated_duration_minutes
                if candidate.estimated_duration_minutes is not None
                else float("inf")
            ),
            candidate.cost_category,
            -candidate.confidence,
            candidate.candidate_id,
        )

    @staticmethod
    def _missing_hypothesis_candidate(definition):
        return ExperimentCandidate(
            candidate_id=(
                "experiment_candidate."
                f"{definition.hypothesis_code.value.lower()}"
            ),
            hypothesis_code=definition.hypothesis_code.value,
            source_action_code=None,
            source_protocol_id=definition.protocol_id,
            hypothesis_status="MISSING",
            support_score=0.0,
            confidence=0.0,
            counter_evidence_count=0,
            missing_fact_count=0,
            informative_value=0.0,
            difficulty=definition.difficulty,
            estimated_duration_minutes=definition.duration_minutes,
            cost_category=definition.cost,
            reversibility=definition.reversibility,
            objective_code=definition.objective_code,
            observable_fact_codes=definition.observable_fact_codes,
            discriminated_hypothesis_codes=tuple(
                item.value
                for item in definition.discriminated_hypothesis_codes
            ),
            prerequisite_codes=definition.prerequisite_parameters,
            unmet_prerequisite_codes=definition.prerequisite_parameters,
            selection_reasons=(),
            ineligibility_reasons=(
                ExperimentSelectionReason.SOURCE_HYPOTHESIS_MISSING,
            ),
            source_analysis_codes=(),
            evidence_codes=(),
            applied_rule_codes=("PLAN_REQUIRE_STRUCTURED_SOURCE",),
            eligible=False,
            controlled_variable_codes=definition.controlled_variable_codes,
            changed_variable_codes=definition.changed_variable_codes,
        )
