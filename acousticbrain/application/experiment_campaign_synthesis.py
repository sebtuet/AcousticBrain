from acousticbrain.models import (
    ComparisonEligibilityStatus,
    ExperimentCampaignAnalysis,
    ExperimentCampaignBranchResult,
    ExperimentCampaignMeasurement,
    ExperimentCampaignMetric,
    ExperimentCampaignStatus,
    ExperimentCampaignTrace,
)


class ExperimentCampaignSynthesisService:
    """Agrège des comparaisons existantes par protocole, sans nouvelle analyse."""

    MODAL_PROTOCOL_ID = "protocol.verify_modal_bass_persistence.v1"
    DECAY_FACT_CODE = "bass_decay.maximum_decay_time_s"
    RULE_CODES = (
        "CAMPAIGN_REQUIRE_EXPLICIT_PROTOCOL",
        "CAMPAIGN_REQUIRE_REFERENCE_BRANCHES",
        "CAMPAIGN_AGGREGATE_EXISTING_COMPARISONS_ONLY",
        "CAMPAIGN_PRESERVE_UNRESOLVED_GLOBAL_COMPONENT",
    )

    def analyze(self, descriptors, comparison_analysis, *, detailed_traceability=False):
        grouped = {}
        for descriptor in descriptors:
            if descriptor.source_protocol_id is not None:
                grouped.setdefault(descriptor.source_protocol_id, []).append(descriptor)
        return tuple(
            self._modal_campaign(
                tuple(items),
                comparison_analysis,
                detailed_traceability=detailed_traceability,
            )
            for protocol_id, items in grouped.items()
            if protocol_id == self.MODAL_PROTOCOL_ID
        )

    def _modal_campaign(
        self,
        descriptors,
        comparison_analysis,
        *,
        detailed_traceability,
    ):
        measurements = tuple(
            ExperimentCampaignMeasurement(
                experiment_id=item.experiment_id,
                role=str(dict(item.comparison_parameters).get("position_role", "UNKNOWN")),
                offset_m=float(
                    dict(item.comparison_parameters).get(
                        "listening_position_offset_m", 0.0
                    )
                ),
                state=item.state.value,
            )
            for item in descriptors
        )
        references = tuple(item for item in measurements if item.role == "REFERENCE")
        reference_id = references[0].experiment_id if len(references) == 1 else None
        local = comparison_analysis.sequence.local_comparisons
        branches = tuple(
            comparison for comparison in local
            if comparison.source_protocol_id == self.MODAL_PROTOCOL_ID
            and comparison.after_experiment_id != reference_id
            and comparison.before_experiment_id == reference_id
        )
        comparable = tuple(
            item for item in branches
            if item.eligibility is ComparisonEligibilityStatus.COMPARABLE
        )
        observation_codes = tuple(dict.fromkeys(
            fact.code
            for comparison in comparable
            for fact in comparison.observed_facts
        ))
        unresolved = tuple(dict.fromkeys(
            item.code
            for comparison in comparable
            for item in comparison.unresolved_discriminations
        ))
        result_codes = [
            code for code in observation_codes
            if code in {
                "BASS_DECAY_VARIES_BY_LISTENING_POSITION",
                "LOCAL_POSITION_EFFECT_SUPPORTED",
            }
        ]
        if "LOCAL_POSITION_EFFECT_VS_GLOBAL_MODE" in unresolved:
            result_codes.append("GLOBAL_MODAL_COMPONENT_NOT_DISCRIMINATED")
        metrics = self._metrics(comparable)
        measurement_by_id = {
            item.experiment_id: item for item in measurements
        }
        branch_results = tuple(
            self._branch_result(item, measurement_by_id[item.after_experiment_id])
            for item in comparable
        )
        complete = (
            reference_id is not None
            and len(measurements) >= 2
            and len(comparable) == len(measurements) - 1
            and bool(metrics)
        )
        local_supported = "LOCAL_POSITION_EFFECT_SUPPORTED" in observation_codes
        global_open = "LOCAL_POSITION_EFFECT_VS_GLOBAL_MODE" in unresolved
        status = (
            ExperimentCampaignStatus.INCOMPLETE
            if not complete
            else ExperimentCampaignStatus.PARTIALLY_RESOLVED
            if local_supported and global_open
            else ExperimentCampaignStatus.RESOLVED
            if local_supported
            else ExperimentCampaignStatus.INCONCLUSIVE
        )
        trace = ExperimentCampaignTrace(
            trace_id="campaign-trace:verify-modal-bass-persistence",
            experiment_ids=tuple(item.experiment_id for item in measurements),
            comparison_result_ids=tuple(item.result_id for item in comparable),
            observation_codes=observation_codes,
            applied_rule_codes=self.RULE_CODES,
        )
        return ExperimentCampaignAnalysis(
            campaign_code="VERIFY_MODAL_BASS_PERSISTENCE",
            protocol_id=self.MODAL_PROTOCOL_ID,
            hypothesis_code="MODAL_BASS_PERSISTENCE",
            objective_code="DETERMINE_BASS_DECAY_LISTENING_POSITION_DEPENDENCE",
            status=status,
            reference_experiment_id=reference_id,
            measurements=measurements,
            branch_results=branch_results,
            result_codes=tuple(dict.fromkeys(result_codes)),
            unresolved_discrimination_codes=unresolved,
            metrics=metrics,
            next_discrimination_code=(
                "CONTROLLED_SOURCE_VARIATION_WITH_FIXED_LISTENER"
                if "SOURCE_EXCITATION_VS_LISTENER_POSITION" in unresolved
                else "CONTROLLED_SOURCE_AND_LISTENER_MATRIX"
                if "LOCAL_POSITION_EFFECT_VS_GLOBAL_MODE" in unresolved
                else None
            ),
            trace=trace,
            detailed_traceability=detailed_traceability,
        )

    def _branch_result(self, comparison, measurement):
        delta = next((
            item for item in comparison.fact_deltas
            if item.fact_code == self.DECAY_FACT_CODE
            and isinstance(item.before, (int, float))
            and isinstance(item.after, (int, float))
        ), None)
        return ExperimentCampaignBranchResult(
            experiment_id=measurement.experiment_id,
            role=measurement.role,
            offset_m=measurement.offset_m,
            acoustic_outcome=comparison.acoustic_outcome.value,
            result_codes=tuple(fact.code for fact in comparison.observed_facts),
            reference_value=float(delta.before) if delta is not None else None,
            observed_value=float(delta.after) if delta is not None else None,
        )

    def _metrics(self, comparisons):
        values = []
        for comparison in comparisons:
            delta = next((
                item for item in comparison.fact_deltas
                if item.fact_code == self.DECAY_FACT_CODE
                and isinstance(item.before, (int, float))
                and isinstance(item.after, (int, float))
            ), None)
            if delta is not None:
                values.append((
                    float(delta.before),
                    float(delta.after),
                    comparison.after_experiment_id,
                ))
        if not values:
            return ()
        reference_values = {item[0] for item in values}
        if len(reference_values) != 1:
            return ()
        reference = reference_values.pop()
        _, best, experiment_id = min(values, key=lambda item: (item[1], item[2]))
        improvement = reference - best
        improvement_percent = improvement / reference * 100.0 if reference else 0.0
        return (ExperimentCampaignMetric(
            code="MAXIMUM_BASS_DECAY_REDUCTION",
            reference_value=reference,
            best_value=best,
            improvement=improvement,
            improvement_percent=improvement_percent,
            unit="SECONDS",
            best_experiment_id=experiment_id,
        ),)
