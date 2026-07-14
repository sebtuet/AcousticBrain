from statistics import fmean

from acousticbrain.models import (
    AcousticHypothesis,
    AcousticReasoningAnalysis,
    EvidenceRole,
    HypothesisCode,
    HypothesisStatus,
    MissingReasoningFact,
    ReasoningEvidence,
    RecommendationPriority,
    VerificationAction,
    VerificationActionType,
)


class AcousticReasoningEngine:
    """Évalue quatre hypothèses à partir de connaissances structurées."""

    STEREO_SYMMETRY_THRESHOLD = 85.0
    ETC_EVENT_COUNT_DIFFERENCE_THRESHOLD = 3
    DRR_BAND_DIFFERENCE_THRESHOLD_DB = 3.0
    BASS_DECAY_DIFFERENCE_THRESHOLD_S = 0.25
    LONG_BASS_DECAY_THRESHOLD_S = 2.0
    SHORT_BASS_DECAY_COUNTER_THRESHOLD_S = 1.0
    DOMINANT_REFLECTION_MAX_DELAY_MS = 20.0
    DOMINANT_REFLECTION_MIN_LEVEL_DB = -20.0
    SUPPORTED_SCORE_THRESHOLD = 70.0
    PLAUSIBLE_SCORE_THRESHOLD = 40.0
    CONTRADICTED_COUNTER_THRESHOLD = 70.0
    COUNTER_PENALTY = 0.5

    def analyze(
        self,
        *,
        stereo=None,
        spatial=None,
        spatial_correlations=None,
        etc=None,
        etc_reflection_correlations=None,
        direct_reverberant=None,
        direct_reverberant_correlations=None,
        bass_decay=None,
        bass_decay_correlations=None,
        modal_density=None,
        sbir=None,
        room_geometry=None,
    ):
        hypotheses = (
            self._asymmetry(
                stereo,
                spatial,
                spatial_correlations,
                etc,
                direct_reverberant,
                bass_decay,
                room_geometry,
            ),
            self._modal_bass(
                bass_decay,
                bass_decay_correlations,
                modal_density,
            ),
            self._early_reflection(
                etc,
                etc_reflection_correlations,
                direct_reverberant_correlations,
            ),
            self._sbir(
                sbir,
                etc_reflection_correlations,
                room_geometry,
            ),
        )
        sources = tuple(
            dict.fromkeys(
                evidence.source_analysis
                for hypothesis in hypotheses
                for collection in (
                    hypothesis.supporting_evidence,
                    hypothesis.counter_evidence,
                    hypothesis.context_evidence,
                )
                for evidence in collection
            )
        )
        return AcousticReasoningAnalysis(
            hypotheses=hypotheses,
            source_analyses=sources,
            confidence=(
                fmean(item.confidence for item in hypotheses)
                if hypotheses
                else 0.0
            ),
        )

    def _asymmetry(
        self,
        stereo,
        spatial,
        spatial_correlations,
        etc,
        direct_reverberant,
        bass_decay,
        room_geometry,
    ):
        code = HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION
        supporting, counter, context, missing, rules = [], [], [], [], []
        required = 3
        available = 0
        if stereo is None:
            missing.append(self._missing("stereo.symmetry_score", "StereoAnalysis", "ASYM_REQUIRE_STEREO"))
        else:
            available += 1
            score = stereo.symmetry_score
            if score < self.STEREO_SYMMETRY_THRESHOLD:
                supporting.append(self._evidence(code, "stereo_symmetry", EvidenceRole.SUPPORTING, "stereo.symmetry_score", "StereoAnalysis", score, 100.0 - score, getattr(stereo, "confidence", 0.0), "STEREO_SYMMETRY_LT_85"))
                rules.append("ASYM_STEREO_LOW_SYMMETRY")
            else:
                counter.append(self._evidence(code, "stereo_symmetry", EvidenceRole.COUNTER_EVIDENCE, "stereo.symmetry_score", "StereoAnalysis", score, score, getattr(stereo, "confidence", 0.0), "STEREO_SYMMETRY_GTE_85"))
        if spatial is None or spatial.pair_analysis is None:
            missing.append(self._missing("spatial.pair_analysis", "SpatialAnalysis", "ASYM_REQUIRE_SPATIAL"))
        else:
            available += 1
            pair = spatial.pair_analysis
            if pair.broadband_level_difference_db is not None:
                context.append(self._evidence(code, "spatial_level", EvidenceRole.CONTEXT, "spatial.broadband_level_difference_db", "SpatialAnalysis", pair.broadband_level_difference_db, min(100.0, abs(pair.broadband_level_difference_db) / 3.0 * 100.0), spatial.confidence, "SPATIAL_LEVEL_REFERENCE"))
            asymmetric = [item for item in getattr(spatial_correlations, "correlations", ()) if "IMBALANCE" in item.code or "ASYMMETRY" in item.code]
            supporting.extend(
                self._evidence(code, f"spatial_{index}", EvidenceRole.SUPPORTING, f"spatial.correlation.{item.code}", "SpatialCorrelationAnalysis", item.score, item.score, item.confidence, "SPATIAL_ASYMMETRY_CORRELATION", correlation=item.code)
                for index, item in enumerate(asymmetric)
            )
            if asymmetric:
                rules.append("ASYM_SPATIAL_CORRELATION")
        if etc is None:
            missing.append(self._missing("etc.channel_specific_event_difference", "ETCAnalysis", "ASYM_REQUIRE_ETC"))
        else:
            available += 1
            difference = abs(etc.left_only_event_count - etc.right_only_event_count)
            role = EvidenceRole.SUPPORTING if difference >= self.ETC_EVENT_COUNT_DIFFERENCE_THRESHOLD else EvidenceRole.COUNTER_EVIDENCE
            target = supporting if role is EvidenceRole.SUPPORTING else counter
            target.append(self._evidence(code, "etc_specific_difference", role, "etc.channel_specific_event_difference", "ETCAnalysis", difference, min(100.0, difference / 8.0 * 100.0) if difference else 100.0, etc.confidence, "ETC_SPECIFIC_DIFFERENCE_GTE_3" if role is EvidenceRole.SUPPORTING else "ETC_SPECIFIC_DIFFERENCE_LT_3"))
        if direct_reverberant is not None:
            count = sum(abs(value) >= self.DRR_BAND_DIFFERENCE_THRESHOLD_DB for value in direct_reverberant.left_right_direct_to_reverberant_differences_db.values())
            if count:
                supporting.append(self._evidence(code, "drr_asymmetric_bands", EvidenceRole.SUPPORTING, "direct_reverberant.asymmetric_band_count", "DirectReverberantAnalysis", count, min(100.0, count / 4.0 * 100.0), direct_reverberant.confidence, "DRR_DIFFERENCE_GTE_3_DB"))
                rules.append("ASYM_DRR_LOCAL_DIFFERENCES")
        if bass_decay is not None:
            differences = [item for item in bass_decay.left_right_band_differences if abs(item.difference_seconds) >= self.BASS_DECAY_DIFFERENCE_THRESHOLD_S]
            if differences:
                supporting.append(self._evidence(code, "bass_decay_asymmetry", EvidenceRole.SUPPORTING, "bass_decay.significant_difference_count", "BassDecayAnalysis", len(differences), min(100.0, len(differences) / 4.0 * 100.0), min(item.confidence for item in differences), "BASS_DECAY_DIFFERENCE_GTE_0_25_S"))
                rules.append("ASYM_BASS_DECAY_DIFFERENCES")
        if room_geometry is None or len(room_geometry.speakers) < 2:
            missing.append(self._missing("room_geometry.stereo_speaker_positions", "RoomGeometry", "ASYM_OPTIONAL_GEOMETRY"))
        else:
            context.append(self._evidence(code, "geometry_source", EvidenceRole.CONTEXT, "room_geometry.source", "RoomGeometry", room_geometry.source.value, 100.0, 100.0, "GEOMETRY_SOURCE_AVAILABLE"))
        return self._finalize(
            code=code,
            phenomenon="speaker_room_asymmetry",
            domains=("STEREO", "SPATIAL", "ETC", "DIRECT_REVERBERANT", "BASS_DECAY"),
            supporting=supporting,
            counter=counter,
            context=context,
            missing=missing,
            rules=rules,
            required_count=required,
            available_required_count=available,
            action_code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
            action_type=VerificationActionType.COMPARE,
            action_target="left_right_measurements_and_placement",
            expected_support="verification.asymmetry_persists_by_channel",
            expected_counter="verification.asymmetry_disappears_after_control",
        )

    def _modal_bass(self, bass_decay, correlations, modal_density):
        code = HypothesisCode.MODAL_BASS_PERSISTENCE
        supporting, counter, context, missing, rules = [], [], [], [], []
        available = 0
        if bass_decay is None:
            missing.append(self._missing("bass_decay.maximum_decay_time", "BassDecayAnalysis", "MODAL_REQUIRE_BASS_DECAY"))
        else:
            available += 1
            times = [item.estimated_decay_time_seconds for item in bass_decay.aggregate_bands if item.estimated_decay_time_seconds is not None]
            if times:
                maximum = max(times)
                if maximum >= self.LONG_BASS_DECAY_THRESHOLD_S:
                    supporting.append(self._evidence(code, "maximum_decay", EvidenceRole.SUPPORTING, "bass_decay.maximum_decay_time", "BassDecayAnalysis", maximum, min(100.0, (maximum - 1.0) / 2.0 * 100.0), bass_decay.confidence, "BASS_DECAY_GTE_2_S"))
                    rules.append("MODAL_LONG_BASS_DECAY")
                elif maximum <= self.SHORT_BASS_DECAY_COUNTER_THRESHOLD_S:
                    counter.append(self._evidence(code, "maximum_decay", EvidenceRole.COUNTER_EVIDENCE, "bass_decay.maximum_decay_time", "BassDecayAnalysis", maximum, 100.0 - maximum * 50.0, bass_decay.confidence, "BASS_DECAY_LTE_1_S"))
        if correlations is None:
            missing.append(self._missing("bass_decay.correlation.SLOW_DECAY_MODAL_INTERACTION", "BassDecayCorrelationAnalysis", "MODAL_REQUIRE_CORRELATION"))
        else:
            available += 1
            modal = next((item for item in correlations.correlations if item.code == "SLOW_DECAY_MODAL_INTERACTION"), None)
            if modal is not None:
                supporting.append(self._evidence(code, "modal_correlation", EvidenceRole.SUPPORTING, "bass_decay.correlation.SLOW_DECAY_MODAL_INTERACTION", "BassDecayCorrelationAnalysis", modal.score, modal.score, modal.confidence, "SLOW_DECAY_MODAL_CORRELATION", correlation=modal.code))
                rules.append("MODAL_STRUCTURED_CORRELATION")
        if modal_density is not None:
            context.append(self._evidence(code, "sparse_modal_bands", EvidenceRole.CONTEXT, "modal_density.sparse_band_count", "ModalDensityAnalysis", len(modal_density.sparse_bands), min(100.0, len(modal_density.sparse_bands) * 25.0), modal_density.confidence, "MODAL_DENSITY_CONTEXT"))
        return self._finalize(code=code, phenomenon="modal_bass_persistence", domains=("BASS_DECAY", "MODAL_DENSITY"), supporting=supporting, counter=counter, context=context, missing=missing, rules=rules, required_count=2, available_required_count=available, action_code="VERIFY_MODAL_BASS_PERSISTENCE", action_type=VerificationActionType.MEASURE, action_target="bass_decay_at_multiple_positions", expected_support="verification.decay_frequency_shifts_by_position", expected_counter="verification.decay_is_position_independent")

    def _early_reflection(self, etc, etc_correlations, drr_correlations):
        code = HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION
        supporting, counter, context, missing, rules = [], [], [], [], []
        available = 0
        geometry_match = None
        if etc is None:
            missing.append(self._missing("etc.available_channels", "ETCAnalysis", "EARLY_REQUIRE_ETC"))
        else:
            available += 1
            context.append(self._evidence(code, "etc_channels", EvidenceRole.CONTEXT, "etc.available_channel_count", "ETCAnalysis", len(etc.available_channels), min(100.0, len(etc.available_channels) / 2.0 * 100.0), etc.confidence, "ETC_CHANNEL_CONTEXT"))
        if etc_correlations is None:
            missing.append(self._missing("etc_reflection.dominant_unmatched_event_count", "ETCReflectionCorrelationAnalysis", "EARLY_REQUIRE_REFLECTION_CORRELATION"))
        else:
            available += 1
            geometry_matches = [
                item
                for item in etc_correlations.correlations
                if item.surface_id is not None
                and item.geometry_path_id is not None
            ]
            geometry_match = max(
                geometry_matches,
                key=lambda item: (
                    item.match_score,
                    -item.timing_error_ms,
                    item.code,
                ),
                default=None,
            )
            if geometry_match is not None:
                supporting.append(self._evidence(
                    code,
                    "geometry_match",
                    EvidenceRole.SUPPORTING,
                    "etc_reflection.geometry_surface_match",
                    "ETCReflectionCorrelationAnalysis",
                    geometry_match.surface_id,
                    geometry_match.match_score,
                    geometry_match.confidence,
                    "EARLY_GEOMETRY_TIMING_COMPATIBLE",
                    correlation=geometry_match.code,
                ))
                context.extend((
                    self._evidence(
                        code,
                        "geometry_delay",
                        EvidenceRole.CONTEXT,
                        "geometry_early_reflection.theoretical_delay_ms",
                        "GeometryEarlyReflectionAnalysis",
                        geometry_match.theoretical_delay_ms,
                        geometry_match.match_score,
                        geometry_match.geometry_confidence or 0.0,
                        "GEOMETRY_IMAGE_SOURCE_FIRST_ORDER",
                        correlation=geometry_match.code,
                    ),
                    self._evidence(
                        code,
                        "geometry_timing_error",
                        EvidenceRole.CONTEXT,
                        "etc_reflection.geometry_timing_error_ms",
                        "ETCReflectionCorrelationAnalysis",
                        geometry_match.timing_error_ms,
                        geometry_match.match_score,
                        geometry_match.confidence,
                        "EARLY_GEOMETRY_TIMING_COMPATIBLE",
                        correlation=geometry_match.code,
                    ),
                ))
                rules.append("EARLY_GEOMETRY_SURFACE_COMPATIBLE")
            important = [event for events in etc_correlations.unmatched_events.values() for event in events if event.delay_ms <= self.DOMINANT_REFLECTION_MAX_DELAY_MS and event.relative_level_db >= self.DOMINANT_REFLECTION_MIN_LEVEL_DB]
            if important:
                supporting.append(self._evidence(code, "dominant_unmatched", EvidenceRole.SUPPORTING, "etc_reflection.dominant_unmatched_event_count", "ETCReflectionCorrelationAnalysis", len(important), min(100.0, len(important) / 10.0 * 100.0), etc_correlations.confidence, "ETC_UNMATCHED_DELAY_LTE_20_LEVEL_GTE_MINUS_20"))
                rules.append("EARLY_DOMINANT_UNMATCHED_EVENTS")
            elif etc_correlations.evaluated_event_count:
                counter.append(self._evidence(code, "dominant_unmatched", EvidenceRole.COUNTER_EVIDENCE, "etc_reflection.dominant_unmatched_event_count", "ETCReflectionCorrelationAnalysis", 0, 100.0, etc_correlations.confidence, "ETC_NO_DOMINANT_UNMATCHED_EVENT"))
        if drr_correlations is not None:
            matches = [item for item in drr_correlations.correlations if item.code == "LOW_DRR_DOMINANT_EARLY_REFLECTIONS"]
            supporting.extend(self._evidence(code, f"drr_{index}", EvidenceRole.SUPPORTING, "direct_reverberant.correlation.LOW_DRR_DOMINANT_EARLY_REFLECTIONS", "DirectReverberantCorrelationAnalysis", item.score, item.score, item.confidence, "DRR_EARLY_REFLECTION_CORRELATION", correlation=item.code) for index, item in enumerate(matches))
            if matches:
                rules.append("EARLY_DRR_CONCORDANCE")
        parameters = {}
        if geometry_match is not None:
            parameters = {
                "surface": geometry_match.surface_id,
                "observed_channel": geometry_match.channel.value,
                "observed_event_delay_ms": geometry_match.measured_delay_ms,
                "observed_event_relative_level_db": (
                    geometry_match.event.relative_level_db
                ),
                "observed_event_sample_index": geometry_match.event.sample_index,
                "theoretical_delay_ms": geometry_match.theoretical_delay_ms,
                "timing_error_ms": geometry_match.timing_error_ms,
                "geometry_uncertainty_ms": geometry_match.geometric_uncertainty_ms,
                "geometry_confidence": geometry_match.geometry_confidence,
                "geometry_path_id": geometry_match.geometry_path_id,
            }
            if geometry_match.impact_point is not None:
                parameters.update({
                    "impact_x_m": geometry_match.impact_point.x_m,
                    "impact_y_m": geometry_match.impact_point.y_m,
                    "impact_z_m": geometry_match.impact_point.z_m,
                })
        return self._finalize(code=code, phenomenon="dominant_early_reflection", domains=("ETC", "DIRECT_REVERBERANT"), supporting=supporting, counter=counter, context=context, missing=missing, rules=rules, required_count=2, available_required_count=available, action_code="VERIFY_DOMINANT_EARLY_REFLECTION", action_type=VerificationActionType.TEMPORARY_MASK, action_target="candidate_early_reflection_surface", expected_support="REFLECTION_DECREASES_AFTER_MASKING", expected_counter="REFLECTION_REMAINS_UNCHANGED_AFTER_MASKING", action_parameters=parameters)

    def _sbir(self, sbir, etc_correlations, room_geometry):
        code = HypothesisCode.SBIR_PLACEMENT_INTERACTION
        supporting, counter, context, missing, rules = [], [], [], [], []
        available = 0
        best = None
        if sbir is None:
            missing.append(self._missing("sbir.best_match", "SBIRAnalysis", "SBIR_REQUIRE_ANALYSIS"))
        else:
            available += 1
            best = sbir.best_match
            if best is not None:
                supporting.append(self._evidence(code, "best_match", EvidenceRole.SUPPORTING, "sbir.best_match_score", "SBIRAnalysis", best.match_score, best.match_score, sbir.confidence, "SBIR_MATCH_AVAILABLE"))
                context.extend((
                    self._evidence(code, "surface", EvidenceRole.CONTEXT, "sbir.reflection_surface", "SBIRAnalysis", best.surface.name, 100.0, sbir.confidence, "SBIR_SURFACE_CONTEXT"),
                    self._evidence(code, "frequency", EvidenceRole.CONTEXT, "sbir.measured_frequency_hz", "SBIRAnalysis", best.measured_frequency, 100.0, sbir.confidence, "SBIR_FREQUENCY_CONTEXT"),
                ))
                rules.append("SBIR_BEST_MATCH_SUPPORT")
            elif sbir.confidence >= 70.0:
                counter.append(self._evidence(code, "best_match", EvidenceRole.COUNTER_EVIDENCE, "sbir.best_match_available", "SBIRAnalysis", False, 100.0, sbir.confidence, "SBIR_NO_MATCH_HIGH_CONFIDENCE"))
        if etc_correlations is not None and best is not None:
            matched = [item for item in etc_correlations.correlations if item.surface is best.surface]
            if matched:
                supporting.append(self._evidence(code, "etc_surface_matches", EvidenceRole.SUPPORTING, "etc_reflection.sbir_surface_match_count", "ETCReflectionCorrelationAnalysis", len(matched), min(100.0, len(matched) * 25.0), max(item.confidence for item in matched), "ETC_SBIR_SAME_SURFACE", correlation=matched[0].code))
                rules.append("SBIR_ETC_SURFACE_CONCORDANCE")
        if room_geometry is None:
            missing.append(self._missing("room_geometry.source", "RoomGeometry", "SBIR_REQUIRE_GEOMETRY_PROVENANCE"))
        else:
            available += 1
            context.append(self._evidence(code, "geometry_source", EvidenceRole.CONTEXT, "room_geometry.source", "RoomGeometry", room_geometry.source.value, 100.0, 100.0, "SBIR_GEOMETRY_SOURCE"))
        parameters = {}
        if best is not None:
            parameters = {"surface": best.surface.name, "measured_frequency_hz": best.measured_frequency, "current_distance_m": best.distance_m}
        return self._finalize(code=code, phenomenon="sbir_placement", domains=("SBIR", "ETC"), supporting=supporting, counter=counter, context=context, missing=missing, rules=rules, required_count=2, available_required_count=available, action_code="VERIFY_SBIR_PLACEMENT", action_type=VerificationActionType.TEMPORARY_MOVE, action_target="speaker_distance_to_candidate_surface", expected_support="verification.sbir_frequency_moves_with_distance", expected_counter="verification.sbir_frequency_is_unchanged", action_parameters=parameters)

    def _finalize(self, *, code, phenomenon, domains, supporting, counter, context, missing, rules, required_count, available_required_count, action_code, action_type, action_target, expected_support, expected_counter, action_parameters=None):
        support_strength = fmean(item.strength for item in supporting) if supporting else 0.0
        counter_strength = fmean(item.strength for item in counter) if counter else 0.0
        support_score = min(100.0, max(0.0, support_strength - self.COUNTER_PENALTY * counter_strength))
        evidence = (*supporting, *counter, *context)
        technical_confidence = fmean(item.confidence for item in evidence) if evidence else 0.0
        coverage = available_required_count / required_count if required_count else 1.0
        confidence = min(100.0, max(0.0, technical_confidence * coverage))
        if counter_strength >= self.CONTRADICTED_COUNTER_THRESHOLD and support_score < self.PLAUSIBLE_SCORE_THRESHOLD:
            status = HypothesisStatus.CONTRADICTED
        elif support_score >= self.SUPPORTED_SCORE_THRESHOLD and not any(item.rule_code.startswith(("ASYM_REQUIRE", "MODAL_REQUIRE", "EARLY_REQUIRE", "SBIR_REQUIRE")) for item in missing):
            status = HypothesisStatus.SUPPORTED
        elif support_score >= self.PLAUSIBLE_SCORE_THRESHOLD:
            status = HypothesisStatus.PLAUSIBLE
        else:
            status = HypothesisStatus.INCONCLUSIVE
        actions = ()
        if supporting:
            evidence_facts = tuple(dict.fromkeys(item.fact_code for item in supporting))
            actions = (
                VerificationAction(
                    code=action_code,
                    action_type=action_type,
                    target=action_target,
                    priority=RecommendationPriority.HIGH if status is HypothesisStatus.SUPPORTED else RecommendationPriority.MEDIUM,
                    confidence=confidence,
                    evidence_fact_codes=evidence_facts,
                    expected_supporting_fact_codes=(expected_support,),
                    expected_counter_fact_codes=(expected_counter,),
                    parameters=action_parameters or {},
                    definitive=False,
                ),
            )
        return AcousticHypothesis(code=code, phenomenon=phenomenon, domain_codes=domains, supporting_evidence=tuple(supporting), counter_evidence=tuple(counter), context_evidence=tuple(context), missing_facts=tuple(missing), applied_rule_codes=tuple(dict.fromkeys(rules)), support_score=support_score, confidence=confidence, status=status, verification_actions=actions)

    @staticmethod
    def _evidence(hypothesis, suffix, role, fact, source, value, strength, confidence, threshold, correlation=None):
        return ReasoningEvidence(code=f"reasoning.{hypothesis.value.lower()}.{suffix}", role=role, fact_code=fact, source_analysis=source, value=value, strength=min(100.0, max(0.0, strength)), confidence=min(100.0, max(0.0, confidence)), threshold_codes=(threshold,), correlation_codes=((correlation,) if correlation else ()))

    @staticmethod
    def _missing(fact, source, rule):
        return MissingReasoningFact(fact_code=fact, source_analysis=source, rule_code=rule)
