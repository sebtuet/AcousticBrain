from acousticbrain.models import (
    EvidenceAcquisitionEffort,
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionPlanSynthesis,
    EvidenceAcquisitionPriority,
    EvidenceAcquisitionStatus,
    EvidenceAcquisitionTestType,
    EvidenceWeightLevel,
    WeightedActionApplicability,
)


class EvidenceAcquisitionPlanner:
    """Transforms explicit blocking factors into diagnostic acquisition plans."""

    def plan(self, reasoning_synthesis, action_synthesis, weighting_synthesis):
        reasonings = {value.reasoning_id: value for value in reasoning_synthesis.reasonings}
        actions = {value.action_id: value for value in action_synthesis.actions}
        plans = []
        for weight in weighting_synthesis.weights:
            if len(weight.action_references) != 1 or len(weight.reasoning_references) != 1:
                raise ValueError("Evidence acquisition requires one action and reasoning per weight.")
            action_id = weight.action_references[0]
            reasoning_id = weight.reasoning_references[0]
            if action_id not in actions:
                raise ValueError(f"Unknown corrective action reference: {action_id}")
            if reasoning_id not in reasonings:
                raise ValueError(f"Unknown reasoning reference: {reasoning_id}")
            action = actions[action_id]
            if reasoning_id not in action.source_reasoning_ids:
                raise ValueError("Evidence acquisition traceability is inconsistent.")
            factors = {value.code: value for value in weight.blocking_factors}
            contradiction = factors.get("CONTRADICTORY_EVIDENCE")
            discrimination = factors.get("INSUFFICIENT_DISCRIMINATION")
            missing = factors.get("MISSING_PARAMETERS")

            if contradiction and not (discrimination and "MODAL_BASS" in reasoning_id):
                plans.append(self._contradiction(weight, action, reasoning_id, contradiction))
            if discrimination:
                targets = tuple(
                    value.factor_id
                    for value in (contradiction, discrimination)
                    if value is not None
                )
                plans.append(self._discrimination(weight, action, reasoning_id, targets))
            if missing:
                parameters = tuple(missing.source_object_ids)
                if "compatible_protocol_or_plan_id" in parameters:
                    plans.append(self._protocol(weight, action, reasoning_id, missing))
                if "additional_supporting_observation" in parameters:
                    plans.append(self._additional_observation(weight, action, reasoning_id, missing))
                    if self._needs_geometry(weight, action, reasoning_id):
                        plans.append(self._geometry(weight, action, reasoning_id, missing))
        return EvidenceAcquisitionPlanSynthesis(tuple(plans))

    def _base(self, weight, action, reasoning_id, suffix, **values):
        priority = self._priority(weight, values["blocking_factor_ids"])
        return EvidenceAcquisitionPlan(
            plan_id=f"EVIDENCE_ACQUISITION_{reasoning_id}_{suffix}",
            reasoning_id=reasoning_id,
            corrective_action_id=action.action_id,
            evidence_weight_id=weight.weight_id,
            priority=priority,
            **values,
        )

    def _contradiction(self, weight, action, reasoning_id, factor):
        stereo = "ASYMMETRIC" in reasoning_id
        return self._base(
            weight,
            action,
            reasoning_id,
            "RESOLVE_CONTRADICTION",
            blocking_factor_ids=(factor.factor_id,),
            objective=f"Acquire repeatable evidence for contradiction {','.join(factor.source_object_ids)}.",
            test_type=(
                EvidenceAcquisitionTestType.CHANNEL_ISOLATION
                if stereo
                else EvidenceAcquisitionTestType.REPEAT_MEASUREMENT
            ),
            instructions=(
                "Measure the left channel independently.",
                "Measure the right channel independently.",
                "Repeat each measurement at the identical documented microphone position.",
                "Compare the same metrics without changing acquisition settings.",
            ),
            required_inputs=("documented_microphone_position", "existing_acquisition_settings"),
            controlled_variables=("gain", "microphone_position", "time_window", "signal_chain"),
            independent_variables=("active_channel",),
            measurements_to_capture=("left_channel_response", "right_channel_response", "repeat_response"),
            expected_observations=("channel_specific_metric", "repeatability_metric"),
            success_criteria=(
                "Repeated channel-isolated observations consistently support one contradictory branch.",
                "Or repeated observations show that neither contradictory branch is stable.",
            ),
            failure_criteria=("Acquisition settings or microphone position differ between repetitions.",),
            resulting_evidence_targets=tuple(factor.source_object_ids),
            estimated_effort=EvidenceAcquisitionEffort.MEDIUM,
            status=EvidenceAcquisitionStatus.READY,
            limitations=("The plan acquires evidence and does not resolve the contradiction itself.",),
        )

    def _discrimination(self, weight, action, reasoning_id, factor_ids):
        protocol_missing = "compatible_protocol_or_plan_id" in action.required_missing_parameters
        return self._base(
            weight,
            action,
            reasoning_id,
            "DISCRIMINATE_HYPOTHESES",
            blocking_factor_ids=factor_ids,
            objective="Discriminate spatial modal persistence from source or placement interaction.",
            test_type=EvidenceAcquisitionTestType.COMPARATIVE_MEASUREMENT,
            instructions=(
                "Measure each speaker independently.",
                "Repeat at the microphone positions defined by the compatible protocol.",
                "Keep acquisition settings unchanged for every comparison.",
                "Compare anomaly frequency, level and decay across sources and positions.",
            ),
            required_inputs=("compatible_protocol_or_plan_id", "protocol_defined_microphone_positions"),
            controlled_variables=("gain", "signal_chain", "time_window", "measurement_method"),
            independent_variables=("active_speaker", "microphone_position"),
            measurements_to_capture=("frequency_response", "anomaly_level", "decay_time"),
            expected_observations=("spatial_change_pattern", "source_tied_pattern"),
            success_criteria=(
                "A position-dependent pattern supports spatial modal behavior.",
                "A source-tied pattern reduces support for spatial modal behavior.",
            ),
            failure_criteria=("Protocol positions or acquisition settings are not comparable.",),
            resulting_evidence_targets=(reasoning_id,),
            estimated_effort=EvidenceAcquisitionEffort.HIGH,
            status=(EvidenceAcquisitionStatus.BLOCKED if protocol_missing else EvidenceAcquisitionStatus.READY),
            limitations=("No microphone distance is invented; positions must come from a compatible protocol.",),
        )

    def _protocol(self, weight, action, reasoning_id, factor):
        return self._base(
            weight,
            action,
            reasoning_id,
            "COMPLETE_PROTOCOL_REFERENCE",
            blocking_factor_ids=(factor.factor_id,),
            objective="Acquire an explicit compatible protocol or plan reference before measurement execution.",
            test_type=EvidenceAcquisitionTestType.PARAMETER_COMPLETION,
            instructions=(
                "Identify an existing compatible protocol or plan by stable id.",
                "Verify that it declares positions, channels, repetitions and acquisition settings.",
                "Do not claim compatibility until the reference passes deterministic validation.",
            ),
            required_inputs=("compatible_protocol_or_plan_id",),
            controlled_variables=("protocol_identity", "protocol_version"),
            independent_variables=("candidate_protocol_reference",),
            measurements_to_capture=("protocol_declaration",),
            expected_observations=("validated_protocol_compatibility",),
            success_criteria=("A referenced protocol or plan declares every required acquisition parameter.",),
            failure_criteria=("No compatible referenced protocol or plan is available.",),
            resulting_evidence_targets=("compatible_protocol_or_plan_id",),
            estimated_effort=EvidenceAcquisitionEffort.LOW,
            status=EvidenceAcquisitionStatus.BLOCKED,
            limitations=("The planner does not invent a scientific protocol.",),
        )

    def _additional_observation(self, weight, action, reasoning_id, factor):
        return self._base(
            weight,
            action,
            reasoning_id,
            "ACQUIRE_SUPPORTING_OBSERVATION",
            blocking_factor_ids=(factor.factor_id,),
            objective="Acquire an additional observation linked to the existing hypothesis.",
            test_type=EvidenceAcquisitionTestType.ADDITIONAL_OBSERVATION,
            instructions=(
                "Capture the measurements required by the existing hypothesis.",
                "Produce an observation using the deterministic observation layer.",
                "Compare observed and expected frequencies only after geometry is available.",
            ),
            required_inputs=("additional_supporting_observation",),
            controlled_variables=("gain", "signal_chain", "microphone_position"),
            independent_variables=("measurement_source",),
            measurements_to_capture=("frequency_response", "source_channel_response"),
            expected_observations=("hypothesis_support", "hypothesis_non_support"),
            success_criteria=("A new deterministic observation explicitly supports or does not support the hypothesis.",),
            failure_criteria=("The new measurement cannot produce a traceable observation.",),
            resulting_evidence_targets=("additional_supporting_observation", reasoning_id),
            estimated_effort=EvidenceAcquisitionEffort.MEDIUM,
            status=EvidenceAcquisitionStatus.READY,
            limitations=("No SBIR conclusion is produced before acquisition and comparison.",),
        )

    def _geometry(self, weight, action, reasoning_id, factor):
        return self._base(
            weight,
            action,
            reasoning_id,
            "ACQUIRE_GEOMETRY",
            blocking_factor_ids=(factor.factor_id,),
            objective="Document geometry required for a future deterministic SBIR comparison.",
            test_type=EvidenceAcquisitionTestType.GEOMETRY_ACQUISITION,
            instructions=(
                "Measure and document both speaker positions relative to room boundaries.",
                "Measure and document the listening and microphone positions.",
                "Record source and microphone heights using declared units.",
            ),
            required_inputs=("measurement_unit", "room_coordinate_reference"),
            controlled_variables=("coordinate_reference", "measurement_unit"),
            independent_variables=("geometry_parameter",),
            measurements_to_capture=(
                "speaker_boundary_distance_m",
                "speaker_position_m",
                "listening_position_m",
                "source_height_m",
                "microphone_height_m",
            ),
            expected_observations=("complete_traceable_room_geometry",),
            success_criteria=("Every required geometry parameter has a value, unit and coordinate reference.",),
            failure_criteria=("At least one required geometry parameter remains undocumented.",),
            resulting_evidence_targets=("room_geometry.stereo_speaker_positions", "sbir.best_match"),
            estimated_effort=EvidenceAcquisitionEffort.LOW,
            status=EvidenceAcquisitionStatus.READY,
            limitations=("Geometry acquisition does not validate the SBIR hypothesis by itself.",),
        )

    @staticmethod
    def _needs_geometry(weight, action, reasoning_id):
        values = (*weight.limitations, *action.limitations)
        return "SBIR" in reasoning_id and any(
            "geometry" in value or "speaker_positions" in value
            for value in values
        )

    @staticmethod
    def _priority(weight, factor_ids):
        if (
            weight.action_applicability is WeightedActionApplicability.BLOCKED
            and weight.evidence_strength is EvidenceWeightLevel.HIGH
        ):
            return EvidenceAcquisitionPriority.CRITICAL
        if any("contradictory_evidence" in value for value in factor_ids):
            return EvidenceAcquisitionPriority.HIGH
        if any("missing_parameters" in value for value in factor_ids):
            return EvidenceAcquisitionPriority.MEDIUM
        return EvidenceAcquisitionPriority.LOW
