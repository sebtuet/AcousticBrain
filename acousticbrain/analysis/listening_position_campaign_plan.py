from acousticbrain.models import (
    ComparisonEligibilityStatus,
    ExperimentKind,
    ExperimentState,
    GeneratedExperimentType,
    ListeningPositionCampaignPlan,
    ListeningPositionCampaignPlanStatus,
    ListeningPositionCampaignStep,
    ListeningPositionCampaignStepExecutionStatus,
    REQUIRED_POSITION_MEASUREMENTS,
    ListeningPositionCampaignInstanceStatus,
)


class ListeningPositionCampaignPlanBuilder:
    """Projects an eligible multi-position candidate into a read-only plan."""

    REFERENCE_SELECTION_RULE_CODES = (
        "REFERENCE_DESCRIPTOR_READY",
        "REFERENCE_MEASUREMENTS_AVAILABLE",
        "REFERENCE_LOCAL_COMPARISON_COMPARABLE",
        "REFERENCE_DECLARATION_STRUCTURED",
        "REFERENCE_CONFIGURATION_COVERAGE_AVAILABLE",
        "LATEST_ADMISSIBLE_CHRONOLOGY_ENTRY",
    )

    def build(self, context):
        candidate = self._source_candidate(context)
        if candidate is None:
            return None

        protocol = getattr(context, "listening_position_sampling_protocol", None)
        instance_analysis = getattr(
            context, "listening_position_campaign_instance_analysis", None
        )
        instance = (
            instance_analysis.instance
            if instance_analysis is not None
            and instance_analysis.status
            is ListeningPositionCampaignInstanceStatus.VALID
            else None
        )
        reasons = []
        prerequisite_candidate_reasons = {
            "MULTI_POSITION_SAMPLING_GEOMETRY_UNAVAILABLE"
        }
        prerequisite_candidate_reasons.update(
            item
            for item in candidate.blocking_reasons
            if item.startswith("REQUIRED_MEASUREMENT_UNAVAILABLE:")
        )
        if any(
            item not in prerequisite_candidate_reasons
            for item in candidate.blocking_reasons
        ):
            reasons.append("SOURCE_CANDIDATE_NOT_ELIGIBLE")
        if instance_analysis is not None and instance is None:
            reasons.extend(instance_analysis.blocking_reasons)
        elif protocol is None or not protocol.definition_completeness.complete:
            reasons.append("MULTI_POSITION_SAMPLING_GEOMETRY_UNAVAILABLE")
        elif (
            candidate.sampling_protocol_id != protocol.protocol_id
            or candidate.sampling_protocol_version != protocol.version
        ):
            reasons.append("MULTI_POSITION_SAMPLING_GEOMETRY_UNAVAILABLE")
        if instance is not None and protocol != instance.to_sampling_protocol():
            reasons.append("CAMPAIGN_INSTANCE_PROTOCOL_MISMATCH")
        if candidate.required_measurements != REQUIRED_POSITION_MEASUREMENTS:
            reasons.append("REQUIRED_MEASUREMENTS_UNAVAILABLE")
        if any(
            item.startswith("REQUIRED_MEASUREMENT_UNAVAILABLE:")
            for item in candidate.blocking_reasons
        ):
            reasons.append("REQUIRED_MEASUREMENTS_UNAVAILABLE")
        if protocol is not None and not protocol.comparability_rule_code:
            reasons.append("COMPARABILITY_RULE_UNAVAILABLE")

        reference = None
        if not reasons:
            reference = self._select_reference(
                context,
                protocol,
                requested_experiment_id=(
                    instance.reference_experiment_id if instance is not None else None
                ),
            )
            if reference is None:
                reasons.append("CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE")

        reasons = list(dict.fromkeys(reasons))
        steps = ()
        if protocol is not None and protocol.definition_completeness.complete:
            try:
                steps = self._steps(
                    protocol,
                    reference.experiment_id if reference is not None else None,
                    blocked=bool(reasons),
                    instance=instance,
                )
            except ValueError:
                reasons = list(dict.fromkeys((*reasons, "CAMPAIGN_STEP_RELATION_INVALID")))
                steps = ()

        status = (
            ListeningPositionCampaignPlanStatus.READY
            if not reasons
            else ListeningPositionCampaignPlanStatus.BLOCKED
        )
        return ListeningPositionCampaignPlan(
            campaign_plan_id=self._plan_id(candidate, protocol, instance),
            protocol_id=protocol.protocol_id if protocol is not None else None,
            protocol_version=protocol.version if protocol is not None else None,
            source_candidate_id=candidate.candidate_id,
            source_instance_id=(instance.instance_id if instance is not None else None),
            source_hypothesis_code=candidate.hypothesis_code,
            reference_experiment_id=(
                reference.experiment_id if reference is not None else None
            ),
            steps=steps,
            status=status,
            blocking_reasons=tuple(reasons),
            causality_status="NOT_ESTABLISHED",
            comparability_rule=(
                protocol.comparability_rule_code if protocol is not None else None
            ),
            controlled_variables=(
                protocol.controlled_variables
                if protocol is not None
                else candidate.controlled_variables
            ),
            required_measurements=candidate.required_measurements,
            reference_selection_rule_codes=self.REFERENCE_SELECTION_RULE_CODES,
        )

    @staticmethod
    def _source_candidate(context):
        analysis = getattr(
            context, "acoustic_hypothesis_experiment_generation_analysis", None
        )
        return next(
            (
                item
                for item in getattr(analysis, "ordered_experiments", ())
                if item.experiment_type
                is GeneratedExperimentType.LISTENING_POSITION_MULTI_POINT
            ),
            None,
        )

    def _select_reference(
        self, context, protocol, *, requested_experiment_id=None
    ):
        descriptors = {
            item.experiment_id: item
            for item in getattr(context, "experiment_descriptors", ())
        }
        comparison = getattr(context, "experiment_comparison_analysis", None)
        sequence = getattr(comparison, "sequence", None)
        chronology = getattr(sequence, "chronology", ())
        comparable = {
            item.after_experiment_id
            for item in getattr(sequence, "local_comparisons", ())
            if item.eligibility is ComparisonEligibilityStatus.COMPARABLE
        }
        for experiment_id in reversed(chronology):
            if (
                requested_experiment_id is not None
                and experiment_id != requested_experiment_id
            ):
                continue
            descriptor = descriptors.get(experiment_id)
            if descriptor is not None and self._reference_is_admissible(
                descriptor, comparable, protocol
            ):
                return descriptor
        return None

    @staticmethod
    def _reference_is_admissible(descriptor, comparable, protocol):
        if (
            descriptor.state is not ExperimentState.READY
            or descriptor.experiment_id not in comparable
        ):
            return False
        channels = {
            getattr(item, "value", str(item)) for item in descriptor.available_channels
        }
        if not set(REQUIRED_POSITION_MEASUREMENTS).issubset(channels):
            return False
        declaration = descriptor.experiment_declaration
        if declaration.experiment_kind is ExperimentKind.UNKNOWN:
            return False
        configuration_facts = set(declaration.modified_variables) | set(
            declaration.controlled_variables
        )
        return set(protocol.controlled_variables).issubset(configuration_facts)

    @staticmethod
    def _steps(
        protocol, reference_experiment_id, *, blocked, instance=None
    ):
        source_positions = instance.positions if instance is not None else protocol.positions
        step_id_by_position = {
            item.position_code: f"campaign-step.{item.position_code}"
            for item in source_positions
        }
        execution_status = (
            ListeningPositionCampaignStepExecutionStatus.BLOCKED
            if blocked
            else ListeningPositionCampaignStepExecutionStatus.PLANNED
        )
        return tuple(
            ListeningPositionCampaignStep(
                step_id=step_id_by_position[position.position_code],
                order_index=(
                    position.order_index
                    if instance is not None
                    else position.acquisition_order
                ),
                position_code=position.position_code,
                position_role=position.position_role,
                longitudinal_offset_m=position.longitudinal_offset_m,
                lateral_offset_m=position.lateral_offset_m,
                vertical_offset_m=position.vertical_offset_m,
                parent_step_id=(
                    step_id_by_position[position.parent_position_code]
                    if position.parent_position_code is not None
                    else None
                ),
                reference_step_id=(
                    step_id_by_position[position.reference_position_code]
                    if position.reference_position_code is not None
                    else None
                ),
                reference_experiment_id=reference_experiment_id,
                modified_variables=(
                    position.modified_variables
                    if instance is not None
                    else protocol.modified_variables
                ),
                controlled_variables=(
                    position.controlled_variables
                    if instance is not None
                    else protocol.controlled_variables
                ),
                required_measurements=position.required_measurements,
                comparability_requirements=(protocol.comparability_rule_code,),
                execution_status=execution_status,
            )
            for position in source_positions
        )

    @staticmethod
    def _plan_id(candidate, protocol, instance):
        protocol_identity = (
            f"{protocol.protocol_id}.v{protocol.version}"
            if protocol is not None
            else "protocol-unavailable"
        )
        instance_identity = (
            instance.instance_id if instance is not None else "instance-unavailable"
        )
        return (
            f"campaign-plan.{candidate.candidate_id}."
            f"{protocol_identity}.{instance_identity}"
        )
