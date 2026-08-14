from dataclasses import replace
from math import isfinite

from acousticbrain.models import (
    AcousticHypothesisExperimentGenerationAnalysis,
    CausalDiscriminationOutcome,
    ExpectedExperimentalObservation,
    ExpectedObservationOutcome,
    GeneratedAcousticExperiment,
    GeneratedAcousticHypothesis,
    GeneratedAcquisitionPosition,
    GeneratedExperimentDifficulty,
    GeneratedExperimentReversibility,
    GeneratedExperimentType,
    GeneratedHypothesisStatus,
    HypothesisCode,
    HypothesisStatus,
    ImpulseChannel,
    ListeningPositionSamplingProtocol,
    ReflectionCandidateGeometricStatus,
    RoomSurfaceKind,
)


class AcousticHypothesisExperimentGenerator:
    """Builds conservative exploratory tests from already-computed analyses."""

    REQUIRED_MEASUREMENTS = ("LEFT", "RIGHT", "STEREO")
    CONTROLLED_SPEAKER_MOVE = (
        "LISTENING_POSITION",
        "LOUDSPEAKER_ORIENTATION",
        "MEASUREMENT_LEVEL",
        "MICROPHONE_POSITION",
        "REW_PARAMETERS",
        "ROOM_CONFIGURATION",
        "SIGNAL_CHAIN_ASSIGNMENT",
    )
    CONTROLLED_TEMPORARY_TREATMENT = (
        "LISTENING_POSITION",
        "LOUDSPEAKER_ASSIGNMENT",
        "LOUDSPEAKER_ORIENTATION",
        "LOUDSPEAKER_POSITION",
        "MEASUREMENT_LEVEL",
        "MICROPHONE_POSITION",
        "REW_PARAMETERS",
        "SIGNAL_CHAIN_ASSIGNMENT",
    )
    CONTROLLED_LISTENING_POSITION = (
        "LOUDSPEAKER_ASSIGNMENT",
        "LOUDSPEAKER_ORIENTATION",
        "LOUDSPEAKER_POSITION",
        "MEASUREMENT_LEVEL",
        "REW_PARAMETERS",
        "ROOM_CONFIGURATION",
        "SIGNAL_CHAIN_ASSIGNMENT",
    )

    _EXECUTED_VARIABLE_TYPES = {
        "TEMPORARY_LEFT_FIRST_REFLECTION_ABSORPTION": (
            GeneratedExperimentType.LEFT_FIRST_REFLECTION_TEMPORARY_ABSORPTION
        ),
        "LEFT_FIRST_REFLECTION_TEMPORARY_ABSORPTION": (
            GeneratedExperimentType.LEFT_FIRST_REFLECTION_TEMPORARY_ABSORPTION
        ),
        "TEMPORARY_RIGHT_FIRST_REFLECTION_ABSORPTION": (
            GeneratedExperimentType.RIGHT_FIRST_REFLECTION_TEMPORARY_ABSORPTION
        ),
        "RIGHT_FIRST_REFLECTION_TEMPORARY_ABSORPTION": (
            GeneratedExperimentType.RIGHT_FIRST_REFLECTION_TEMPORARY_ABSORPTION
        ),
        "FRONT_WALL_TEMPORARY_ABSORPTION": (
            GeneratedExperimentType.FRONT_WALL_TEMPORARY_ABSORPTION
        ),
        "REAR_LISTENING_AREA_TEMPORARY_ABSORPTION": (
            GeneratedExperimentType.REAR_LISTENING_AREA_TEMPORARY_ABSORPTION
        ),
        "LISTENING_POSITION_MULTI_POINT": GeneratedExperimentType.LISTENING_POSITION_MULTI_POINT,
        "MULTIPLE_LISTENING_POSITIONS": GeneratedExperimentType.LISTENING_POSITION_MULTI_POINT,
        "LEFT_SPEAKER_POSITION_FORWARD": GeneratedExperimentType.LEFT_SPEAKER_FORWARD,
        "LEFT_SPEAKER_POSITION_BACKWARD": GeneratedExperimentType.LEFT_SPEAKER_BACKWARD,
        "RIGHT_SPEAKER_POSITION_FORWARD": GeneratedExperimentType.RIGHT_SPEAKER_FORWARD,
        "RIGHT_SPEAKER_POSITION_BACKWARD": GeneratedExperimentType.RIGHT_SPEAKER_BACKWARD,
        "BOTH_SPEAKERS_POSITION_FORWARD": GeneratedExperimentType.BOTH_SPEAKERS_FORWARD,
        "BOTH_SPEAKERS_POSITION_BACKWARD": GeneratedExperimentType.BOTH_SPEAKERS_BACKWARD,
    }

    def generate(self, context) -> AcousticHypothesisExperimentGenerationAnalysis:
        reasoning = getattr(context, "acoustic_reasoning_analysis", None)
        if reasoning is None:
            return self._empty()

        source_hypotheses = {
            item.code.value: item
            for item in reasoning.hypotheses
            if item.code in set(HypothesisCode)
        }
        executed, mixed = self._experiment_history(context)
        causal = getattr(context, "causal_discrimination_analysis", None)
        asymmetry_discriminated = bool(
            causal is not None
            and causal.outcome is CausalDiscriminationOutcome.DISCRIMINATED
        )

        experiments = []
        by_hypothesis = {code.value: [] for code in HypothesisCode}

        sbir = source_hypotheses.get(HypothesisCode.SBIR_PLACEMENT_INTERACTION.value)
        if sbir is not None and self._is_candidate_hypothesis(sbir):
            candidate = self._sbir_experiment(context, sbir)
            if candidate is not None and candidate.experiment_type not in executed:
                experiments.append(candidate)
                by_hypothesis[sbir.code.value].append(candidate.candidate_id)

        reflection = source_hypotheses.get(
            HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION.value
        )
        if reflection is not None and self._is_candidate_hypothesis(reflection):
            candidate = self._reflection_experiment(context, reflection, executed)
            if candidate is not None:
                experiments.append(candidate)
                by_hypothesis[reflection.code.value].append(candidate.candidate_id)
                if self._reflection_also_tests_asymmetry(candidate, source_hypotheses):
                    by_hypothesis[
                        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION.value
                    ].append(candidate.candidate_id)
                    candidate = replace(
                        candidate,
                        rationale_codes=tuple(
                            dict.fromkeys((*candidate.rationale_codes, "MULTI_PURPOSE_ASYMMETRY_TEST"))
                        ),
                    )
                    experiments[-1] = candidate

        modal = source_hypotheses.get(HypothesisCode.MODAL_BASS_PERSISTENCE.value)
        if modal is not None and self._modal_test_is_informative(context, modal):
            experiment_type = GeneratedExperimentType.LISTENING_POSITION_MULTI_POINT
            if experiment_type not in executed:
                candidate = self._modal_experiment(context, modal)
                experiments.append(candidate)
                by_hypothesis[modal.code.value].append(candidate.candidate_id)

        experiments = self._deduplicate(experiments)
        available_measurements = self._available_measurements(context)
        experiments = [
            self._block_missing_measurements(item, available_measurements)
            for item in experiments
        ]
        experiments = self._rank_and_limit(experiments)
        retained_ids = {item.candidate_id for item in experiments}
        by_hypothesis = {
            code: [candidate_id for candidate_id in ids if candidate_id in retained_ids]
            for code, ids in by_hypothesis.items()
        }

        generated_hypotheses = []
        for code in (
            HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION.value,
            HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION.value,
            HypothesisCode.MODAL_BASS_PERSISTENCE.value,
            HypothesisCode.SBIR_PLACEMENT_INTERACTION.value,
        ):
            source = source_hypotheses.get(code)
            if source is None:
                continue
            generated_hypotheses.append(
                self._hypothesis(
                    source,
                    tuple(by_hypothesis[code]),
                    experiments,
                    mixed=mixed,
                    asymmetry_discriminated=asymmetry_discriminated,
                )
            )

        generated_hypotheses.sort(
            key=lambda item: (
                {
                    GeneratedHypothesisStatus.PLAUSIBLE: 0,
                    GeneratedHypothesisStatus.WEAKLY_PLAUSIBLE: 1,
                    GeneratedHypothesisStatus.INSUFFICIENT_EVIDENCE: 2,
                    GeneratedHypothesisStatus.CONTRADICTED: 3,
                }[item.status],
                item.hypothesis_code,
            )
        )
        recommended = next((item.candidate_id for item in experiments if item.eligible), None)
        return AcousticHypothesisExperimentGenerationAnalysis(
            hypotheses=tuple(generated_hypotheses[:5]),
            ordered_experiments=tuple(experiments),
            recommended_candidate_id=recommended,
            applied_rule_codes=(
                "PR048_EXISTING_ANALYSES_ONLY",
                "PR048_SINGLE_VARIABLE_ONLY",
                "PR048_EXECUTED_EXPERIMENT_DEDUPLICATION",
                "PR048_DETERMINISTIC_INFORMATION_RANKING_V1",
                "PR048_CAUSALITY_NEVER_ESTABLISHED",
            ),
            source_analysis_codes=self._source_analysis_codes(context),
        )

    @staticmethod
    def _empty():
        return AcousticHypothesisExperimentGenerationAnalysis(
            hypotheses=(), ordered_experiments=(), recommended_candidate_id=None,
            applied_rule_codes=("PR048_NO_REASONING_ANALYSIS",), source_analysis_codes=(),
        )

    @staticmethod
    def _is_candidate_hypothesis(hypothesis):
        return hypothesis.status is not HypothesisStatus.CONTRADICTED and bool(
            hypothesis.supporting_evidence
        )

    def _experiment_history(self, context):
        executed = set()
        for descriptor in getattr(context, "experiment_descriptors", ()):
            variables = (
                *getattr(descriptor, "declared_change_codes", ()),
                *getattr(descriptor.experiment_declaration, "modified_variables", ()),
            )
            executed.update(filter(None, (self._map_variable(value) for value in variables)))
        mixed = set()
        comparison = getattr(context, "experiment_comparison_analysis", None)
        sequence = getattr(comparison, "sequence", None)
        for result in getattr(sequence, "local_comparisons", ()):
            result_types = {
                self._map_variable(value) for value in result.modified_variables
            }
            if getattr(result.acoustic_outcome, "value", None) == "MIXED":
                mixed.update(item for item in result_types if item is not None)
        return executed, mixed

    @staticmethod
    def _source_analysis_codes(context):
        fields = (
            ("acoustic_reasoning_analysis", "AcousticReasoningAnalysis"),
            ("experiment_comparison_analysis", "ExperimentComparisonAnalysis"),
            ("causal_discrimination_analysis", "CausalDiscriminationAnalysis"),
            ("room_geometry", "RoomGeometry"),
            (
                "material_aware_reflection_candidate_analysis",
                "MaterialAwareReflectionCandidateAnalysis",
            ),
            (
                "sbir_geometry_correlation_analysis",
                "SBIRGeometryCorrelationAnalysis",
            ),
            ("modal_density_analysis", "ModalDensityAnalysis"),
            ("bass_decay_analysis", "BassDecayAnalysis"),
        )
        return tuple(
            code for field, code in fields if getattr(context, field, None) is not None
        )

    def _map_variable(self, value):
        normalized = str(value).upper()
        if normalized in self._EXECUTED_VARIABLE_TYPES:
            return self._EXECUTED_VARIABLE_TYPES[normalized]
        for marker, experiment_type in self._EXECUTED_VARIABLE_TYPES.items():
            if normalized.startswith(marker + "_") and normalized.endswith(("MM", "CM")):
                return experiment_type
        return None

    def _sbir_experiment(self, context, hypothesis):
        analysis = getattr(context, "sbir_geometry_correlation_analysis", None)
        match = getattr(analysis, "best_match", None)
        if match is None:
            return None
        source = match.candidate
        surface = getattr(source.surface, "name", str(source.surface))
        if surface != "FRONT_WALL":
            return None
        speaker = source.speaker_id.upper()
        if "LEFT" in speaker:
            experiment_type = GeneratedExperimentType.LEFT_SPEAKER_FORWARD
            target = "LEFT_SPEAKER"
        elif "RIGHT" in speaker:
            experiment_type = GeneratedExperimentType.RIGHT_SPEAKER_FORWARD
            target = "RIGHT_SPEAKER"
        else:
            return None
        frequency = float(match.observed_dip.frequency)
        frequency_regions = ()
        uncertainty_hz = getattr(source, "frequency_uncertainty_hz", None)
        if self._is_non_negative_number(uncertainty_hz):
            frequency_regions = ((
                max(0.0, frequency - float(uncertainty_hz)),
                frequency + float(uncertainty_hz),
            ),)
        step_distance_m = self._structured_positive_parameter(
            hypothesis, "proposed_displacement_m"
        )
        blocking_reasons = (
            ()
            if step_distance_m is not None
            else ("STRUCTURED_STEP_DISTANCE_UNAVAILABLE",)
        )
        observations = self._frequency_shift_observations("SBIR", frequency)
        return self._experiment(
            candidate_id=f"generated.{experiment_type.value.lower()}.sbir",
            hypothesis_code=hypothesis.code.value,
            experiment_type=experiment_type,
            target=target,
            movement_axis="LONGITUDINAL",
            movement_direction="FORWARD_AWAY_FROM_FRONT_WALL",
            step_distance_m=step_distance_m,
            modified_variable=f"{target}_LONGITUDINAL_POSITION",
            controlled_variables=self.CONTROLLED_SPEAKER_MOVE,
            observations=observations,
            frequency_regions=frequency_regions,
            time_regions=(),
            reversibility=GeneratedExperimentReversibility.HIGH,
            difficulty=GeneratedExperimentDifficulty.EASY,
            blocking_reasons=blocking_reasons,
            rationale=(
                "SBIR_GEOMETRY_FREQUENCY_MATCH",
                (
                    "STRUCTURED_STEP_DISTANCE_REUSED"
                    if step_distance_m is not None
                    else "STRUCTURED_STEP_DISTANCE_UNAVAILABLE"
                ),
                "LOCALIZED_FREQUENCY_EFFECT_ONLY",
            ),
        )

    def _reflection_experiment(self, context, hypothesis, executed):
        analysis = getattr(context, "material_aware_reflection_candidate_analysis", None)
        candidates = sorted(
            (
                item for item in getattr(analysis, "candidates", ())
                if item.geometric_status is ReflectionCandidateGeometricStatus.ACCEPTED
            ),
            key=lambda item: (item.informative_rank or 10**6, item.candidate_id),
        )
        geometry = getattr(context, "room_geometry", None)
        surface_kinds = {
            item.surface_id: item.kind for item in getattr(geometry, "surfaces", ())
        }
        mapping = {
            RoomSurfaceKind.LEFT_WALL: (
                GeneratedExperimentType.LEFT_FIRST_REFLECTION_TEMPORARY_ABSORPTION,
                "LEFT_FIRST_REFLECTION_AREA",
            ),
            RoomSurfaceKind.RIGHT_WALL: (
                GeneratedExperimentType.RIGHT_FIRST_REFLECTION_TEMPORARY_ABSORPTION,
                "RIGHT_FIRST_REFLECTION_AREA",
            ),
            RoomSurfaceKind.FRONT_WALL: (
                GeneratedExperimentType.FRONT_WALL_TEMPORARY_ABSORPTION,
                "FRONT_WALL_CANDIDATE_REGION",
            ),
            RoomSurfaceKind.REAR_WALL: (
                GeneratedExperimentType.REAR_LISTENING_AREA_TEMPORARY_ABSORPTION,
                "REAR_LISTENING_AREA",
            ),
        }
        paths = {
            item.path_id: item
            for item in getattr(
                getattr(context, "geometry_early_reflection_analysis", None), "paths", ()
            )
        }
        for item in candidates:
            kind = surface_kinds.get(item.surface_id)
            selection = mapping.get(kind)
            if selection is None or selection[0] in executed:
                continue
            experiment_type, target = selection
            path = paths.get(item.path_id)
            time_regions = ()
            if path is not None and self._is_non_negative_number(
                path.uncertainty_ms
            ):
                uncertainty = float(path.uncertainty_ms)
                time_regions = ((
                    max(0.0, path.theoretical_delay_ms - uncertainty),
                    path.theoretical_delay_ms + uncertainty,
                ),)
            observations = self._reflection_observations()
            return self._experiment(
                candidate_id=f"generated.{experiment_type.value.lower()}.reflection",
                hypothesis_code=hypothesis.code.value,
                experiment_type=experiment_type,
                target=target,
                movement_axis=None,
                movement_direction=None,
                step_distance_m=None,
                modified_variable="TEMPORARY_ABSORPTION_AT_ONE_CANDIDATE_SURFACE",
                controlled_variables=self.CONTROLLED_TEMPORARY_TREATMENT,
                observations=observations,
                frequency_regions=(),
                time_regions=time_regions,
                reversibility=GeneratedExperimentReversibility.HIGH,
                difficulty=GeneratedExperimentDifficulty.EASY,
                blocking_reasons=(),
                rationale=(
                    "IDENTIFIED_SINGLE_REFLECTION_SURFACE",
                    "REVERSIBLE_LOCALIZED_TEMPORARY_TREATMENT",
                    "NO_GLOBAL_IMPROVEMENT_GUARANTEE",
                ),
            )
        return None

    @staticmethod
    def _reflection_also_tests_asymmetry(candidate, hypotheses):
        asymmetry = hypotheses.get(HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION.value)
        return bool(
            asymmetry is not None
            and asymmetry.status is not HypothesisStatus.CONTRADICTED
            and candidate.experiment_type in {
                GeneratedExperimentType.LEFT_FIRST_REFLECTION_TEMPORARY_ABSORPTION,
                GeneratedExperimentType.RIGHT_FIRST_REFLECTION_TEMPORARY_ABSORPTION,
            }
        )

    def _modal_test_is_informative(self, context, hypothesis):
        modal = getattr(context, "modal_density_analysis", None)
        bass = getattr(context, "bass_decay_analysis", None)
        return bool(
            self._status(hypothesis) in {
                GeneratedHypothesisStatus.PLAUSIBLE,
                GeneratedHypothesisStatus.WEAKLY_PLAUSIBLE,
            }
            and (
                getattr(modal, "sparse_bands", ())
                or getattr(modal, "dense_bands", ())
                or any(
                    band.estimated_decay_time_seconds is not None
                    for band in getattr(bass, "aggregate_bands", ())
                )
            )
        )

    def _modal_experiment(self, context, hypothesis):
        regions = []
        modal = getattr(context, "modal_density_analysis", None)
        for band in (*getattr(modal, "sparse_bands", ()), *getattr(modal, "dense_bands", ())):
            regions.append((float(band.minimum_hz), float(band.maximum_hz)))
        if not regions:
            bass = getattr(context, "bass_decay_analysis", None)
            for band in getattr(bass, "aggregate_bands", ()):
                if band.estimated_decay_time_seconds is not None:
                    regions.append((float(band.minimum_frequency_hz), float(band.maximum_frequency_hz)))
        observations = self._modal_observations()
        positions, reference_position_id, sampling_protocol = (
            self._multi_position_acquisition(context)
        )
        blocking_reasons = (
            ()
            if positions
            else ("MULTI_POSITION_SAMPLING_GEOMETRY_UNAVAILABLE",)
        )
        return self._experiment(
            candidate_id="generated.listening_position_multi_point.modal",
            hypothesis_code=hypothesis.code.value,
            experiment_type=GeneratedExperimentType.LISTENING_POSITION_MULTI_POINT,
            target="LISTENING_AREA",
            movement_axis=None,
            movement_direction=None,
            step_distance_m=None,
            modified_variable=(
                sampling_protocol.modified_variables[0]
                if sampling_protocol is not None
                else "LISTENING_POSITION_SAMPLING"
            ),
            controlled_variables=(
                sampling_protocol.controlled_variables
                if sampling_protocol is not None
                else self.CONTROLLED_LISTENING_POSITION
            ),
            required_measurements=(
                sampling_protocol.positions[0].required_measurements
                if sampling_protocol is not None
                else self.REQUIRED_MEASUREMENTS
            ),
            observations=observations,
            frequency_regions=tuple(sorted(set(regions)))[:5],
            time_regions=(),
            reversibility=GeneratedExperimentReversibility.HIGH,
            difficulty=GeneratedExperimentDifficulty.EASY,
            blocking_reasons=blocking_reasons,
            rationale=(
                "LOW_FREQUENCY_SPATIAL_VARIATION_TEST",
                "NO_SPEAKER_DIRECTION_INVENTED",
                "NO_PRECISE_DISTANCE_WITHOUT_CONTRACT",
            ),
            acquisition_positions=positions,
            reference_position_id=reference_position_id,
            comparability_rule_code=(
                sampling_protocol.comparability_rule_code
                if sampling_protocol is not None
                else None
            ),
            sampling_protocol_id=(
                sampling_protocol.protocol_id
                if sampling_protocol is not None
                else None
            ),
            sampling_protocol_version=(
                sampling_protocol.version
                if sampling_protocol is not None
                else None
            ),
            sampling_completion_condition_codes=(
                sampling_protocol.completion_condition_codes
                if sampling_protocol is not None
                else ()
            ),
        )

    def _experiment(
        self, *, candidate_id, hypothesis_code, experiment_type, target,
        movement_axis, movement_direction, step_distance_m, modified_variable,
        controlled_variables, observations, frequency_regions, time_regions,
        reversibility, difficulty, blocking_reasons, rationale,
        required_measurements=None,
        acquisition_positions=(), reference_position_id=None,
        comparability_rule_code=None,
        sampling_protocol_id=None, sampling_protocol_version=None,
        sampling_completion_condition_codes=(),
    ):
        information = 35.0
        information += 15.0 if not blocking_reasons else 0.0
        information += 10.0 if reversibility is GeneratedExperimentReversibility.HIGH else 5.0
        information += 10.0 if difficulty is GeneratedExperimentDifficulty.EASY else 5.0
        information += min(20.0, 5.0 * len(observations))
        information += 10.0 if frequency_regions or time_regions else 0.0
        return GeneratedAcousticExperiment(
            candidate_id=candidate_id,
            hypothesis_code=hypothesis_code,
            experiment_type=experiment_type,
            target=target,
            movement_axis=movement_axis,
            movement_direction=movement_direction,
            step_distance_m=step_distance_m,
            modified_variables=(modified_variable,),
            controlled_variables=tuple(controlled_variables),
            required_measurements=(
                tuple(required_measurements)
                if required_measurements is not None
                else self.REQUIRED_MEASUREMENTS
            ),
            expected_observations=tuple(observations),
            expected_frequency_regions=tuple(frequency_regions),
            expected_time_regions=tuple(time_regions),
            information_value=min(100.0, information),
            reversibility=reversibility,
            difficulty=difficulty,
            blocking_reasons=tuple(blocking_reasons),
            rationale_codes=tuple(rationale),
            acquisition_positions=tuple(acquisition_positions),
            reference_position_id=reference_position_id,
            comparability_rule_code=comparability_rule_code,
            sampling_protocol_id=sampling_protocol_id,
            sampling_protocol_version=sampling_protocol_version,
            sampling_completion_condition_codes=tuple(
                sampling_completion_condition_codes
            ),
        )

    def _hypothesis(
        self, source, candidate_ids, experiments, *, mixed, asymmetry_discriminated
    ):
        status = self._status(source)
        uncertainty = []
        if source.code is HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION and mixed & {
            GeneratedExperimentType.LEFT_FIRST_REFLECTION_TEMPORARY_ABSORPTION,
            GeneratedExperimentType.RIGHT_FIRST_REFLECTION_TEMPORARY_ABSORPTION,
            GeneratedExperimentType.FRONT_WALL_TEMPORARY_ABSORPTION,
            GeneratedExperimentType.REAR_LISTENING_AREA_TEMPORARY_ABSORPTION,
        }:
            if status is GeneratedHypothesisStatus.PLAUSIBLE:
                status = GeneratedHypothesisStatus.WEAKLY_PLAUSIBLE
            uncertainty.append("PRIOR_RELATED_TEMPORARY_TREATMENT_MIXED")
        if source.code is HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION:
            uncertainty.append(
                "CAUSAL_PROTOCOL_ALREADY_DISCRIMINATED"
                if asymmetry_discriminated
                else "CAUSAL_PROTOCOL_NOT_YET_DISCRIMINATED"
            )
        candidate_set = set(candidate_ids)
        observations = tuple(
            dict.fromkeys(
                code
                for experiment in experiments
                if experiment.candidate_id in candidate_set
                for code in experiment.expected_observation_codes
            )
        )
        if not candidate_ids and status in {
            GeneratedHypothesisStatus.PLAUSIBLE,
            GeneratedHypothesisStatus.WEAKLY_PLAUSIBLE,
        }:
            uncertainty.append("NO_SAFE_CONCRETE_EXPERIMENT_FROM_AVAILABLE_STRUCTURE")
        return GeneratedAcousticHypothesis(
            hypothesis_code=source.code.value,
            status=status,
            supporting_fact_codes=tuple(item.fact_code for item in source.supporting_evidence),
            contradicting_fact_codes=tuple(item.fact_code for item in source.counter_evidence),
            missing_fact_codes=tuple(item.fact_code for item in source.missing_facts),
            experiment_candidate_ids=tuple(candidate_ids),
            expected_observation_codes=observations,
            rationale_codes=tuple(source.applied_rule_codes),
            uncertainty_reasons=tuple(dict.fromkeys(uncertainty)),
        )

    @staticmethod
    def _status(source):
        if source.status is HypothesisStatus.CONTRADICTED:
            return GeneratedHypothesisStatus.CONTRADICTED
        if source.status in {HypothesisStatus.SUPPORTED, HypothesisStatus.PLAUSIBLE}:
            return GeneratedHypothesisStatus.PLAUSIBLE
        if source.supporting_evidence or source.context_evidence:
            return GeneratedHypothesisStatus.WEAKLY_PLAUSIBLE
        return GeneratedHypothesisStatus.INSUFFICIENT_EVIDENCE

    @staticmethod
    def _deduplicate(experiments):
        result = {}
        for item in experiments:
            key = (item.experiment_type, item.target, item.step_distance_m)
            existing = result.get(key)
            if existing is None or item.information_value > existing.information_value:
                result[key] = item
        return list(result.values())

    @staticmethod
    def _rank_and_limit(experiments):
        return sorted(
            experiments,
            key=lambda item: (
                -item.information_value,
                item.experiment_type.value,
                item.candidate_id,
            ),
        )[:5]

    @staticmethod
    def _structured_positive_parameter(hypothesis, parameter_code):
        for action in hypothesis.verification_actions:
            value = action.parameters.get(parameter_code)
            if (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and isfinite(value)
                and value > 0.0
            ):
                return float(value)
        return None

    @staticmethod
    def _is_non_negative_number(value):
        return bool(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            and value >= 0.0
        )

    @staticmethod
    def _available_measurements(context):
        quality = getattr(context, "measurement_quality_analysis", None)
        measurement_set = getattr(quality, "measurement_set_quality", None)
        if measurement_set is not None:
            channels = set(measurement_set.available_channels)
        else:
            channels = set()
            project = getattr(context, "project", None)
            getter = getattr(project, "get_impulse_response", None)
            if callable(getter):
                channels = {
                    channel
                    for channel in (
                        ImpulseChannel.LEFT,
                        ImpulseChannel.RIGHT,
                        ImpulseChannel.STEREO,
                    )
                    if getter(channel) is not None
                }
        return {getattr(channel, "value", str(channel)) for channel in channels}

    def _block_missing_measurements(self, experiment, available_measurements):
        missing = tuple(
            measurement
            for measurement in experiment.required_measurements
            if measurement not in available_measurements
        )
        if not missing:
            return experiment
        reasons = tuple(
            dict.fromkeys(
                (
                    *experiment.blocking_reasons,
                    *(f"REQUIRED_MEASUREMENT_UNAVAILABLE:{item}" for item in missing),
                )
            )
        )
        information_value = experiment.information_value
        if not experiment.blocking_reasons:
            information_value = max(0.0, information_value - 15.0)
        return replace(
            experiment,
            blocking_reasons=reasons,
            information_value=information_value,
        )

    def _multi_position_acquisition(self, context):
        protocol = getattr(context, "listening_position_sampling_protocol", None)
        if (
            not isinstance(protocol, ListeningPositionSamplingProtocol)
            or not protocol.definition_completeness.complete
        ):
            return (), None, None
        reference = protocol.reference_position
        positions = tuple(
            GeneratedAcquisitionPosition(
                position_id=position.position_code,
                role=position.position_role,
                longitudinal_offset_m=position.longitudinal_offset_m,
                lateral_offset_m=position.lateral_offset_m,
                vertical_offset_m=position.vertical_offset_m,
                parent_position_id=position.parent_position_code,
                reference_position_id=position.reference_position_code,
                required_measurements=position.required_measurements,
                acquisition_order=position.acquisition_order,
            )
            for position in protocol.positions
        )
        return positions, reference.position_code, protocol

    @staticmethod
    def _frequency_shift_observations(prefix, frequency):
        label = f"{frequency:.2f}HZ"
        return (
            ExpectedExperimentalObservation(
                f"{prefix}_LOCAL_ANOMALY_FREQUENCY_SHIFTS_{label}",
                ExpectedObservationOutcome.SUPPORTING,
                ("frequency.left", "frequency.right", "frequency.stereo"),
            ),
            ExpectedExperimentalObservation(
                f"{prefix}_LOCAL_ANOMALY_DOES_NOT_SHIFT_{label}",
                ExpectedObservationOutcome.CONTRADICTING,
                ("frequency.left", "frequency.right", "frequency.stereo"),
            ),
            ExpectedExperimentalObservation(
                f"{prefix}_LOCAL_CHANGE_BELOW_THRESHOLD_{label}",
                ExpectedObservationOutcome.NEUTRAL,
                ("frequency.left", "frequency.right", "frequency.stereo"),
            ),
            ExpectedExperimentalObservation(
                f"{prefix}_MEASUREMENT_NOT_COMPARABLE_{label}",
                ExpectedObservationOutcome.INCONCLUSIVE,
                ("measurement.readiness",),
            ),
        )

    @staticmethod
    def _reflection_observations():
        return (
            ExpectedExperimentalObservation(
                "TARGET_ETC_EVENT_DECREASES_LOCALLY",
                ExpectedObservationOutcome.SUPPORTING,
                ("etc.event_relative_level_db", "direct_reverberant.band_difference_db"),
            ),
            ExpectedExperimentalObservation(
                "TARGET_ETC_EVENT_REMAINS_UNCHANGED",
                ExpectedObservationOutcome.CONTRADICTING,
                ("etc.event_relative_level_db",),
            ),
            ExpectedExperimentalObservation(
                "ONLY_NON_TARGET_TEMPORAL_FACTS_CHANGE",
                ExpectedObservationOutcome.NEUTRAL,
                ("etc.event_relative_level_db", "clarity.band_metrics"),
            ),
            ExpectedExperimentalObservation(
                "TARGET_ETC_EVENT_NOT_RELIABLY_MEASURABLE",
                ExpectedObservationOutcome.INCONCLUSIVE,
                ("measurement.readiness",),
            ),
        )

    @staticmethod
    def _modal_observations():
        return (
            ExpectedExperimentalObservation(
                "LOW_FREQUENCY_ANOMALY_VARIES_BY_LISTENING_POSITION",
                ExpectedObservationOutcome.SUPPORTING,
                ("frequency.response", "bass_decay.estimated_decay_time_s"),
            ),
            ExpectedExperimentalObservation(
                "LOW_FREQUENCY_ANOMALY_IS_SPATIALLY_STABLE",
                ExpectedObservationOutcome.CONTRADICTING,
                ("frequency.response", "bass_decay.estimated_decay_time_s"),
            ),
            ExpectedExperimentalObservation(
                "LOW_FREQUENCY_VARIATION_BELOW_THRESHOLD",
                ExpectedObservationOutcome.NEUTRAL,
                ("frequency.response",),
            ),
            ExpectedExperimentalObservation(
                "MULTI_POSITION_MEASUREMENTS_NOT_COMPARABLE",
                ExpectedObservationOutcome.INCONCLUSIVE,
                ("measurement.readiness",),
            ),
        )
