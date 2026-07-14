from dataclasses import dataclass

from acousticbrain.models import (
    ComparableExperimentFact,
    ComparisonEligibilityStatus,
    ComparisonIneligibilityReason,
    ExperimentComparisonAnalysis,
    ExperimentComparisonSequence,
    ExperimentComparisonTrace,
    ExperimentComparisonType,
    ExperimentCounterFact,
    ExperimentAcousticOutcome,
    ExperimentEvolutionOutcome,
    ExperimentEvolutionResult,
    ExperimentFactChange,
    ExperimentFactDelta,
    ExperimentState,
    HypothesisEvolutionResult,
    ObservedExperimentFact,
    UnresolvedDiscrimination,
)

from .optimization_session import OptimizationSessionService


@dataclass(frozen=True)
class AnalyzedExperiment:
    descriptor: object
    context: object | None
    state: object | None
    facts: tuple[ComparableExperimentFact, ...]
    technical_confidence: float | None


class ExperimentFactProjector:
    """Adapte des résultats structurés existants, sans nouvelle analyse acoustique."""

    SCORE_THRESHOLD = 1.0
    SUPPORT_THRESHOLD = 2.0
    DOMAIN_READINESS_FAMILY = {
        "STEREO": "FREQUENCY",
        "SBIR": "FREQUENCY",
        "MODAL_DENSITY": "FREQUENCY",
    }

    def project(self, context) -> tuple[ComparableExperimentFact, ...]:
        facts = []
        readiness = self._readiness(context)
        global_analysis = context.global_analysis
        for domain in global_analysis.domains:
            facts.append(self._fact(
                f"global.domain.{domain.code.lower()}.score",
                domain.score,
                "SCORE",
                domain.code,
                domain.source_analysis,
                self.SCORE_THRESHOLD,
                True,
                readiness.get(
                    self.DOMAIN_READINESS_FAMILY.get(domain.code, domain.code),
                    "AVAILABLE",
                ),
            ))
        reasoning = context.acoustic_reasoning_analysis
        if reasoning is not None:
            for hypothesis in reasoning.hypotheses:
                code = hypothesis.code.value
                facts.append(self._fact(
                    f"hypothesis.{code}.support_score",
                    hypothesis.support_score,
                    "SCORE",
                    "ACOUSTIC_REASONING",
                    "AcousticReasoningAnalysis",
                    self.SUPPORT_THRESHOLD,
                    True,
                    "AVAILABLE",
                    (code, *hypothesis.applied_rule_codes),
                ))
        self._append_specific_facts(context, facts, readiness)
        return tuple(sorted(facts, key=lambda item: item.code))

    @staticmethod
    def _fact(code, value, unit, family, source, threshold, higher, readiness,
              provenance=()):
        return ComparableExperimentFact(
            code=code,
            value=value,
            unit=unit,
            family=family,
            semantic=code,
            source_analysis=source,
            threshold=threshold,
            higher_is_better=higher,
            readiness=readiness,
            provenance_codes=tuple(provenance),
        )

    @staticmethod
    def _readiness(context):
        analysis = context.measurement_readiness_analysis
        if analysis is None:
            return {}
        return {
            item.family.value: item.status.value
            for item in analysis.analyses
        }

    def _append_specific_facts(self, context, facts, readiness):
        spatial = context.spatial_analysis
        pair = spatial.pair_analysis if spatial is not None else None
        if pair is not None:
            facts.append(self._fact(
                "spatial.left_right.level_difference_abs_db",
                abs(pair.broadband_level_difference_db)
                if pair.broadband_level_difference_db is not None else None,
                "DB", "SPATIAL", "SpatialAnalysis", 0.5, False,
                readiness.get("SPATIAL", "AVAILABLE"),
            ))
        drr = context.direct_reverberant_analysis
        if drr is not None:
            values = tuple(drr.left_right_direct_to_reverberant_differences_db.values())
            facts.append(self._fact(
                "direct_reverberant.left_right.maximum_difference_abs_db",
                max(map(abs, values)) if values else None,
                "DB", "DIRECT_REVERBERANT", "DirectReverberantAnalysis",
                0.5, False, readiness.get("DIRECT_REVERBERANT", "AVAILABLE"),
            ))
        decay = context.bass_decay_analysis
        if decay is not None:
            differences = decay.left_right_band_differences
            facts.append(self._fact(
                "bass_decay.left_right.maximum_difference_abs_s",
                max((abs(item.difference_seconds) for item in differences), default=None),
                "SECONDS", "BASS_DECAY", "BassDecayAnalysis", 0.05, False,
                readiness.get("BASS_DECAY", "AVAILABLE"),
            ))
            facts.append(self._fact(
                "bass_decay.maximum_decay_time_s",
                max((
                    item.estimated_decay_time_seconds
                    for item in decay.aggregate_bands
                    if item.estimated_decay_time_seconds is not None
                ), default=None),
                "SECONDS", "BASS_DECAY", "BassDecayAnalysis", 0.05, False,
                readiness.get("BASS_DECAY", "AVAILABLE"),
            ))
        etc = context.etc_analysis
        if etc is not None:
            facts.append(self._fact(
                "etc.channel_specific_event_count",
                etc.left_only_event_count + etc.right_only_event_count,
                "COUNT", "ETC", "ETCAnalysis", 1.0, False,
                readiness.get("ETC", "AVAILABLE"),
            ))
        sbir_geometry = getattr(
            context, "sbir_geometry_correlation_analysis", None
        )
        geometry_match = (
            sbir_geometry.best_match if sbir_geometry is not None else None
        )
        sbir = context.sbir
        if geometry_match is not None:
            facts.append(self._fact(
                "sbir.target_null_frequency_hz",
                geometry_match.observed_dip.frequency,
                "HZ", "SBIR", "SBIRGeometryCorrelationAnalysis", 2.0, None,
                readiness.get("FREQUENCY", "AVAILABLE"),
            ))
            facts.append(self._fact(
                "sbir.target_null_prominence_db",
                geometry_match.observed_dip.prominence,
                "DB", "SBIR", "SBIRGeometryCorrelationAnalysis", 1.0, False,
                readiness.get("FREQUENCY", "AVAILABLE"),
            ))
        elif sbir is not None:
            facts.append(self._fact(
                "sbir.target_null_frequency_hz",
                sbir.best_match.measured_frequency if sbir.best_match else None,
                "HZ", "SBIR", "SBIRAnalysis", 2.0, None,
                readiness.get("FREQUENCY", "AVAILABLE"),
            ))
            facts.append(self._fact(
                "sbir.target_null_prominence_db",
                sbir.best_match.peak.prominence if sbir.best_match else None,
                "DB", "SBIR", "SBIRAnalysis", 1.0, False,
                readiness.get("FREQUENCY", "AVAILABLE"),
            ))


class AutomaticExperimentComparisonService:
    """Relie la chronologie PR-027 aux snapshots/comparaisons PR-025."""

    RULES = (
        "COMPARE_SAME_CODE_UNIT_FAMILY_SEMANTIC",
        "REQUIRE_AVAILABLE_READINESS",
        "APPLY_EXPLICIT_FACT_THRESHOLD",
        "LIMIT_CAUSAL_INFERENCE_TO_DECLARED_PROTOCOL",
    )
    DISCRIMINATIONS = {
        "ASYMMETRIC_SPEAKER_ROOM_INTERACTION": (
            ("LOUDSPEAKER_VS_ROOM_SIDE", "CONTROLLED_LOUDSPEAKER_SWAP"),
            ("LOUDSPEAKER_VS_SIGNAL_CHAIN", "CONTROLLED_SIGNAL_CHAIN_SWAP"),
            ("SIGNAL_CHAIN_VS_ROOM_SIDE", "CONTROLLED_SIGNAL_CHAIN_SWAP"),
        ),
        "MODAL_BASS_PERSISTENCE": (
            (
                "LOCAL_POSITION_EFFECT_VS_GLOBAL_MODE",
                "CONTROLLED_SOURCE_AND_LISTENER_MATRIX",
            ),
            ("SOURCE_EXCITATION_VS_LISTENER_POSITION", "CONTROLLED_SOURCE_POSITION"),
        ),
        "DOMINANT_EARLY_REFLECTION_INTERACTION": (
            ("CANDIDATE_SURFACE_VS_OTHER_SURFACE", "CONTROLLED_SURFACE_MASK"),
            ("REFLECTION_VS_MEASUREMENT_VARIABILITY", "REPEATED_MEASUREMENT"),
        ),
        "SBIR_PLACEMENT_INTERACTION": (
            ("SBIR_VS_ROOM_MODE", "MULTIPLE_LISTENING_POSITIONS"),
            ("CANDIDATE_SURFACE_VS_OTHER_BOUNDARY", "CONTROLLED_BOUNDARY_DISTANCE"),
        ),
    }

    def __init__(self, fact_projector=None):
        self.fact_projector = fact_projector or ExperimentFactProjector()

    def analyze(
        self,
        acoustic_session,
        analyzed_contexts,
        *,
        optimization_session=None,
        detailed_traceability=False,
    ):
        analyzed = {
            item.descriptor.experiment_id: self._analyzed(item, analyzed_contexts)
            for item in acoustic_session.experiments
        }
        descriptors = acoustic_session.descriptors
        chronology = tuple(item.experiment_id for item in descriptors)
        baseline = acoustic_session.baseline
        local = []
        cumulative = []
        for index, after in enumerate(descriptors):
            if after.experiment_type.value == "BASELINE":
                continue
            parent, reasons = self._local_parent(after, descriptors, index)
            metadata = self._metadata(after, optimization_session)
            local.append(self._compare(
                analyzed.get(parent.experiment_id) if parent else None,
                analyzed[after.experiment_id],
                ExperimentComparisonType.LOCAL,
                tuple(reasons),
                metadata,
            ))
            cumulative.append(self._compare(
                analyzed.get(baseline.descriptor.experiment_id)
                if baseline is not None else None,
                analyzed[after.experiment_id],
                ExperimentComparisonType.CUMULATIVE,
                (() if baseline is not None else (
                    ComparisonIneligibilityReason.INVALID_CHRONOLOGY,
                )),
                metadata,
            ))
        return ExperimentComparisonAnalysis(
            sequence=ExperimentComparisonSequence(
                chronology=chronology,
                local_comparisons=tuple(local),
                cumulative_comparisons=tuple(cumulative),
            ),
            source_analysis_codes=(
                "ExperimentDiscoveryService",
                "OptimizationSessionService",
                "AutomaticExperimentComparisonService",
            ),
            detailed_traceability=detailed_traceability,
        )

    def _analyzed(self, imported, contexts):
        descriptor = imported.descriptor
        context = contexts.get(descriptor.experiment_id)
        if context is None:
            return AnalyzedExperiment(descriptor, None, None, (), None)
        state = OptimizationSessionService.snapshot_analysis(
            context, state_id=f"physical:{descriptor.experiment_id}"
        )
        confidence = getattr(context.confidence_analysis, "score", None)
        return AnalyzedExperiment(
            descriptor, context, state, self.fact_projector.project(context), confidence
        )

    @staticmethod
    def _local_parent(after, descriptors, index):
        parents = after.parent_experiment_ids
        if len(parents) > 1:
            return None, (ComparisonIneligibilityReason.AMBIGUOUS_PARENT,)
        if len(parents) == 1:
            matches = [item for item in descriptors if item.experiment_id == parents[0]]
            if not matches:
                return None, (ComparisonIneligibilityReason.UNKNOWN_PARENT,)
            parent = matches[0]
            if descriptors.index(parent) >= index:
                return parent, (ComparisonIneligibilityReason.INVALID_CHRONOLOGY,)
            return parent, ()
        if index == 0:
            return None, (ComparisonIneligibilityReason.INVALID_CHRONOLOGY,)
        return descriptors[index - 1], ()

    @staticmethod
    def _metadata(descriptor, optimization_session):
        if descriptor.source_protocol_id or descriptor.source_hypothesis_code:
            return (
                descriptor.source_protocol_id,
                descriptor.source_hypothesis_code,
                descriptor.declared_change_codes,
                descriptor.required_comparison_fact_codes,
                descriptor.comparison_parameters,
            )
        if optimization_session is not None:
            matches = [
                item.protocol for item in optimization_session.iterations
                if item.protocol.experiment_id == descriptor.experiment_id
            ]
            if len(matches) == 1:
                protocol = matches[0]
                return (
                    protocol.experiment_id,
                    protocol.hypothesis_code,
                    (),
                    protocol.fact_codes,
                    (),
                )
        return (
            None,
            None,
            (),
            descriptor.required_comparison_fact_codes,
            descriptor.comparison_parameters,
        )

    def _compare(self, before, after, comparison_type, initial_reasons, metadata):
        before_id = before.descriptor.experiment_id if before else "UNRESOLVED"
        after_id = after.descriptor.experiment_id
        reasons = list(initial_reasons)
        if before is None or before.context is None:
            reasons.append(ComparisonIneligibilityReason.INSUFFICIENT_BEFORE_DATA)
        if after.context is None:
            reasons.append(ComparisonIneligibilityReason.INSUFFICIENT_AFTER_DATA)
        if before and before.descriptor.state is not ExperimentState.READY:
            reasons.append(ComparisonIneligibilityReason.EXPERIMENT_INCOMPLETE)
        if after.descriptor.state is not ExperimentState.READY:
            reasons.append(ComparisonIneligibilityReason.EXPERIMENT_INCOMPLETE)
        deltas, fact_reasons, unavailable = self._fact_deltas(before, after)
        reasons.extend(fact_reasons)
        (
            source_protocol,
            hypothesis,
            declared_changes,
            required_facts,
            experiment_parameters,
        ) = metadata
        comparable_codes = {item.fact_code for item in deltas}
        if any(code not in comparable_codes for code in required_facts):
            reasons.append(ComparisonIneligibilityReason.REQUIRED_FACT_UNAVAILABLE)
        if (
            before is not None
            and declared_changes
            and before.descriptor.content_hash == after.descriptor.content_hash
        ):
            reasons.append(ComparisonIneligibilityReason.IDENTICAL_CONTENT)
        reasons = tuple(dict.fromkeys(reasons))
        observed, counters = self._observations(
            hypothesis,
            deltas,
            declared_changes,
            protocol_observations=(
                comparison_type is ExperimentComparisonType.LOCAL
            ),
        )
        outcome, initial_status = self._outcome(
            hypothesis, before, after, deltas, reasons, declared_changes
        )
        acoustic_outcome = self._acoustic_outcome(
            deltas, reasons, required_facts
        )
        experimental_result_codes = self._experimental_results(observed)
        causal_reassignment = bool(
            hypothesis == "ASYMMETRIC_SPEAKER_ROOM_INTERACTION"
            and {
                "CONTROLLED_SIGNAL_CHAIN_SWAP",
                "CONTROLLED_LOUDSPEAKER_SWAP",
            }
            & set(declared_changes)
        )
        unresolved = self._unresolved(hypothesis, declared_changes)
        eligibility = (
            ComparisonEligibilityStatus.NOT_COMPARABLE
            if reasons else ComparisonEligibilityStatus.COMPARABLE
        )
        result_id = f"comparison:{comparison_type.value.lower()}:{before_id}:{after_id}"
        trace = ExperimentComparisonTrace(
            trace_id=f"trace:{result_id}",
            comparison_type=comparison_type,
            before_experiment_id=before_id,
            after_experiment_id=after_id,
            before_file_hash=before.descriptor.content_hash if before else "",
            after_file_hash=after.descriptor.content_hash,
            before_fact_codes=tuple(item.code for item in before.facts) if before else (),
            after_fact_codes=tuple(item.code for item in after.facts),
            delta_fact_codes=tuple(item.fact_code for item in deltas),
            observed_fact_codes=tuple(item.code for item in observed),
            hypothesis_code=hypothesis,
            evolution_outcome=outcome,
            acoustic_outcome=acoustic_outcome,
            experimental_result_codes=experimental_result_codes,
            unresolved_discrimination_codes=tuple(item.code for item in unresolved),
        )
        confidence_values = tuple(
            value for value in (
                before.technical_confidence if before else None,
                after.technical_confidence,
            ) if isinstance(value, (int, float))
        )
        return ExperimentEvolutionResult(
            result_id=result_id,
            before_experiment_id=before_id,
            after_experiment_id=after_id,
            comparison_type=comparison_type,
            source_protocol_id=source_protocol,
            source_hypothesis_code=hypothesis,
            experiment_parameters=experiment_parameters,
            initial_hypothesis_status=initial_status,
            outcome=outcome,
            acoustic_outcome=acoustic_outcome,
            experimental_result_codes=experimental_result_codes,
            eligibility=eligibility,
            ineligibility_reasons=reasons,
            fact_deltas=deltas,
            observed_facts=observed,
            counter_facts=counters,
            unavailable_fact_codes=unavailable,
            unresolved_discriminations=unresolved,
            applied_rule_codes=(
                *self.RULES,
                *(("CAUSAL_REASSIGNMENT_CANNOT_REFUTE_GENERIC_HYPOTHESIS",)
                  if causal_reassignment else ()),
            ),
            applied_threshold_codes=tuple(
                f"{item.fact_code}:{item.threshold:g}" for item in deltas
            ),
            technical_confidence=min(confidence_values) if confidence_values else None,
            provenance_codes=tuple(dict.fromkeys((
                *(
                    f"{before_id}:{item.relative_path}:{item.sha256}"
                    for item in (before.descriptor.available_files if before else ())
                ),
                *(
                    f"{after_id}:{item.relative_path}:{item.sha256}"
                    for item in after.descriptor.available_files
                ),
                *(code for item in deltas for code in item.source_analysis_codes),
            ))),
            trace=trace,
        )

    def _fact_deltas(self, before, after):
        if before is None:
            return (), (), ()
        old = {item.code: item for item in before.facts}
        new = {item.code: item for item in after.facts}
        deltas = []
        reasons = []
        unavailable = list(sorted(old.keys() ^ new.keys()))
        for code in sorted(old.keys() & new.keys()):
            left, right = old[code], new[code]
            if left.unit != right.unit:
                reasons.append(ComparisonIneligibilityReason.INCOMPATIBLE_UNIT)
                continue
            if left.family != right.family:
                reasons.append(ComparisonIneligibilityReason.INCOMPATIBLE_FAMILY)
                continue
            if left.semantic != right.semantic:
                reasons.append(ComparisonIneligibilityReason.INCOMPATIBLE_SEMANTICS)
                continue
            if "BLOCKED" in (left.readiness, right.readiness):
                reasons.append(ComparisonIneligibilityReason.READINESS_BLOCKED)
                unavailable.append(code)
                continue
            if left.value is None or right.value is None:
                unavailable.append(code)
                continue
            delta = self._numeric_delta(left.value, right.value)
            threshold = max(left.threshold, right.threshold)
            if delta is None or abs(delta) < threshold:
                change = ExperimentFactChange.UNCHANGED
            elif left.higher_is_better is None:
                change = ExperimentFactChange.CHANGED
            else:
                improvement = (delta > 0) == left.higher_is_better
                change = ExperimentFactChange.IMPROVED if improvement else ExperimentFactChange.DEGRADED
            deltas.append(ExperimentFactDelta(
                fact_code=code, before=left.value, after=right.value,
                delta=delta, unit=left.unit, change=change, threshold=threshold,
                source_analysis_codes=tuple(dict.fromkeys((
                    left.source_analysis, right.source_analysis,
                    *left.provenance_codes, *right.provenance_codes,
                ))),
            ))
        if not deltas and not reasons:
            reasons.append(ComparisonIneligibilityReason.NO_USABLE_MEASUREMENT)
        return tuple(deltas), tuple(dict.fromkeys(reasons)), tuple(unavailable)

    @staticmethod
    def _numeric_delta(before, after):
        if all(isinstance(value, (int, float)) and not isinstance(value, bool)
               for value in (before, after)):
            return float(after - before)
        return None

    @staticmethod
    def _observations(
        hypothesis,
        deltas,
        declared_changes=(),
        *,
        protocol_observations=True,
    ):
        if hypothesis is None:
            return (), ()
        mapping = {
            "ASYMMETRIC_SPEAKER_ROOM_INTERACTION": {
                "spatial.left_right.level_difference_abs_db": "SPATIAL_ASYMMETRY_DECREASED",
                "direct_reverberant.left_right.maximum_difference_abs_db": "DRR_ASYMMETRY_DECREASED",
                "bass_decay.left_right.maximum_difference_abs_s": "BASS_DECAY_ASYMMETRY_DECREASED",
            },
            "MODAL_BASS_PERSISTENCE": {
                "bass_decay.maximum_decay_time_s": "BASS_DECAY_REDUCED_AT_TARGET_BANDS",
            },
            "DOMINANT_EARLY_REFLECTION_INTERACTION": {
                "etc.channel_specific_event_count": "UNMATCHED_EVENT_COUNT_DECREASED",
            },
            "SBIR_PLACEMENT_INTERACTION": {
                "sbir.target_null_frequency_hz": "TARGET_NULL_FREQUENCY_SHIFTED",
                "sbir.target_null_prominence_db": "TARGET_NULL_DEPTH_REDUCED",
            },
        }.get(hypothesis, {})
        counter_mapping = {
            "SPATIAL_ASYMMETRY_DECREASED": "SPATIAL_ASYMMETRY_INCREASED",
            "DRR_ASYMMETRY_DECREASED": "DRR_ASYMMETRY_INCREASED",
            "BASS_DECAY_ASYMMETRY_DECREASED": "BASS_DECAY_ASYMMETRY_INCREASED",
            "BASS_DECAY_REDUCED_AT_TARGET_BANDS": "BASS_DECAY_INCREASED_AT_TARGET_BANDS",
            "UNMATCHED_EVENT_COUNT_DECREASED": "UNMATCHED_EVENT_COUNT_INCREASED",
            "TARGET_NULL_DEPTH_REDUCED": "TARGET_NULL_DEPTH_INCREASED",
        }
        observed = []
        counters = []
        for delta in deltas:
            code = mapping.get(delta.fact_code)
            if code is None:
                continue
            if code == "TARGET_NULL_FREQUENCY_SHIFTED":
                controlled_speaker_move = bool({
                    "CONTROLLED_SPEAKER_POSITION",
                    "TEMPORARY_SPEAKER_MOVE",
                }.intersection(declared_changes))
                if delta.change is not ExperimentFactChange.UNCHANGED:
                    observed.append(ObservedExperimentFact(
                        (
                            "SBIR_MOVES_WITH_SPEAKER"
                            if controlled_speaker_move else code
                        ),
                        (delta.fact_code,),
                        delta.source_analysis_codes,
                    ))
                else:
                    observed.append(ObservedExperimentFact(
                        (
                            "SBIR_REMAINS_FIXED"
                            if controlled_speaker_move
                            else "TARGET_NULL_UNCHANGED"
                        ),
                        (delta.fact_code,),
                        delta.source_analysis_codes,
                    ))
                continue
            if delta.change is ExperimentFactChange.UNCHANGED:
                stable = {
                    "BASS_DECAY_REDUCED_AT_TARGET_BANDS": "BASS_DECAY_STABLE_AT_TARGET_BANDS",
                    "TARGET_NULL_FREQUENCY_SHIFTED": "TARGET_NULL_UNCHANGED",
                }.get(code)
                if stable:
                    observed.append(ObservedExperimentFact(
                        stable, (delta.fact_code,), delta.source_analysis_codes
                    ))
                continue
            if delta.change is ExperimentFactChange.IMPROVED:
                observed.append(ObservedExperimentFact(
                    code, (delta.fact_code,), delta.source_analysis_codes
                ))
            else:
                counters.append(ExperimentCounterFact(
                    counter_mapping.get(code, code),
                    (delta.fact_code,),
                    delta.source_analysis_codes,
                ))
        if (
            hypothesis == "ASYMMETRIC_SPEAKER_ROOM_INTERACTION"
            and "LEFT_RIGHT_REMEASUREMENT" in declared_changes
        ):
            asymmetry = tuple(item for item in deltas if item.fact_code in {
                "spatial.left_right.level_difference_abs_db",
                "direct_reverberant.left_right.maximum_difference_abs_db",
                "bass_decay.left_right.maximum_difference_abs_s",
            })
            provenance = tuple(dict.fromkeys(
                code for item in asymmetry for code in item.source_analysis_codes
            ))
            if asymmetry and all(
                item.change is ExperimentFactChange.UNCHANGED for item in asymmetry
            ):
                if any(
                    isinstance(item.before, (int, float))
                    and abs(item.before) >= item.threshold
                    for item in asymmetry
                ):
                    observed.append(ObservedExperimentFact(
                        "LEFT_RIGHT_DIFFERENCE_REPRODUCIBLE",
                        tuple(item.fact_code for item in asymmetry),
                        provenance,
                    ))
                observed.append(ObservedExperimentFact(
                    "CHANNEL_SPECIFIC_PATTERN_STABLE",
                    tuple(item.fact_code for item in asymmetry),
                    provenance,
                ))
            elif asymmetry:
                observed.append(ObservedExperimentFact(
                    "CHANNEL_SPECIFIC_PATTERN_CHANGED",
                    tuple(item.fact_code for item in asymmetry),
                    provenance,
                ))
        if (
            hypothesis == "MODAL_BASS_PERSISTENCE"
            and "MULTIPLE_LISTENING_POSITIONS" in declared_changes
            and protocol_observations
        ):
            decay = next((
                item for item in deltas
                if item.fact_code == "bass_decay.maximum_decay_time_s"
            ), None)
            if decay is not None and decay.change is not ExperimentFactChange.UNCHANGED:
                observed.extend((
                    ObservedExperimentFact(
                        "BASS_DECAY_VARIES_BY_LISTENING_POSITION",
                        (decay.fact_code,),
                        decay.source_analysis_codes,
                    ),
                    ObservedExperimentFact(
                        "LOCAL_POSITION_EFFECT_SUPPORTED",
                        (decay.fact_code,),
                        decay.source_analysis_codes,
                    ),
                ))
        return tuple(observed), tuple(counters)

    @staticmethod
    def _acoustic_outcome(deltas, reasons, required_fact_codes=()):
        if reasons:
            return ExperimentAcousticOutcome.INCONCLUSIVE
        required = set(required_fact_codes)
        scoped = tuple(
            item for item in deltas
            if item.fact_code in required
        ) if required else tuple(
            item for item in deltas
            if not item.fact_code.startswith("hypothesis.")
        )
        if not scoped:
            return ExperimentAcousticOutcome.INCONCLUSIVE
        changes = {item.change for item in scoped}
        improved = ExperimentFactChange.IMPROVED in changes
        degraded = ExperimentFactChange.DEGRADED in changes
        if improved and degraded:
            return ExperimentAcousticOutcome.MIXED
        if improved:
            return ExperimentAcousticOutcome.IMPROVED
        if degraded:
            return ExperimentAcousticOutcome.DEGRADED
        if changes <= {ExperimentFactChange.UNCHANGED}:
            return ExperimentAcousticOutcome.UNCHANGED
        return ExperimentAcousticOutcome.MIXED

    @staticmethod
    def _experimental_results(observed):
        discriminating_codes = (
            "LOCAL_POSITION_EFFECT_SUPPORTED",
        )
        available = {item.code for item in observed}
        return tuple(code for code in discriminating_codes if code in available)

    @staticmethod
    def _outcome(hypothesis, before, after, deltas, reasons, declared_changes=()):
        if reasons or hypothesis is None or before is None or before.state is None or after.state is None:
            return ExperimentEvolutionOutcome.INCONCLUSIVE, None
        old = next((item for item in before.state.hypotheses if item.code == hypothesis), None)
        new = next((item for item in after.state.hypotheses if item.code == hypothesis), None)
        initial_status = old.status if old else None
        support_delta = next((
            item for item in deltas
            if item.fact_code == f"hypothesis.{hypothesis}.support_score"
        ), None)
        evolution = OptimizationSessionService.compare_hypothesis(
            hypothesis, before.state, after.state
        )
        causal_reassignment = bool(
            hypothesis == "ASYMMETRIC_SPEAKER_ROOM_INTERACTION"
            and {
                "CONTROLLED_SIGNAL_CHAIN_SWAP",
                "CONTROLLED_LOUDSPEAKER_SWAP",
            }
            & set(declared_changes)
        )
        if new is not None and new.status == "CONTRADICTED" and causal_reassignment:
            return (
                ExperimentEvolutionOutcome.WEAKER
                if support_delta is not None
                and support_delta.change is ExperimentFactChange.DEGRADED
                else ExperimentEvolutionOutcome.INCONCLUSIVE,
                initial_status,
            )
        if new is not None and new.status == "CONTRADICTED":
            return ExperimentEvolutionOutcome.CONTRADICTED, initial_status
        if support_delta is not None and support_delta.change is ExperimentFactChange.UNCHANGED \
                and old is not None and new is not None and old.status == new.status:
            return ExperimentEvolutionOutcome.UNCHANGED, initial_status
        return {
            HypothesisEvolutionResult.REINFORCED: ExperimentEvolutionOutcome.STRONGER,
            HypothesisEvolutionResult.WEAKENED: ExperimentEvolutionOutcome.WEAKER,
            HypothesisEvolutionResult.REFUTED: ExperimentEvolutionOutcome.CONTRADICTED,
            HypothesisEvolutionResult.UNCHANGED: ExperimentEvolutionOutcome.UNCHANGED,
        }[evolution.result], initial_status

    def _unresolved(self, hypothesis, declared_changes):
        return tuple(
            UnresolvedDiscrimination(code, (required,))
            for code, required in self.DISCRIMINATIONS.get(hypothesis, ())
            if required not in declared_changes
        )
