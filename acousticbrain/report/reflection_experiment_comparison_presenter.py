from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedObservedReflectionDifference:
    observable_code: str
    unit: str
    baseline_value: float
    intervention_value: float
    signed_difference: float
    absolute_difference: float
    baseline_provenance_codes: tuple[str, ...]
    intervention_provenance_codes: tuple[str, ...]


@dataclass(frozen=True)
class PresentedControlledReflectionExperimentComparison:
    comparison_id: str
    experiment_declaration_id: str
    proposal_id: str
    status: str
    temporal_window_code: str
    baseline_measurement_reference_ids: tuple[str, ...]
    intervention_measurement_reference_ids: tuple[str, ...]
    observed_differences: tuple[PresentedObservedReflectionDifference, ...]
    reason_codes: tuple[str, ...]
    causality_status: str
    ranking_impact: str
    recommendation_impact: str
    eligibility_impact: str
    source_analysis_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]


class ControlledReflectionExperimentComparisonPresenter:
    def present(self, context):
        return tuple(
            PresentedControlledReflectionExperimentComparison(
                comparison_id=item.comparison_id,
                experiment_declaration_id=item.experiment_declaration_id,
                proposal_id=item.proposal_id,
                status=item.status.value,
                temporal_window_code=item.temporal_window_code,
                baseline_measurement_reference_ids=(
                    item.baseline_measurement_reference_ids
                ),
                intervention_measurement_reference_ids=(
                    item.intervention_measurement_reference_ids
                ),
                observed_differences=tuple(
                    PresentedObservedReflectionDifference(
                        observable_code=difference.observable_code,
                        unit=difference.unit,
                        baseline_value=difference.baseline_value,
                        intervention_value=difference.intervention_value,
                        signed_difference=difference.signed_difference,
                        absolute_difference=difference.absolute_difference,
                        baseline_provenance_codes=(
                            difference.baseline_provenance_codes
                        ),
                        intervention_provenance_codes=(
                            difference.intervention_provenance_codes
                        ),
                    )
                    for difference in item.observed_differences
                ),
                reason_codes=item.reason_codes,
                causality_status=item.causality_status.value,
                ranking_impact=item.ranking_impact.value,
                recommendation_impact=item.recommendation_impact.value,
                eligibility_impact=item.eligibility_impact.value,
                source_analysis_codes=item.source_analysis_codes,
                applied_rule_codes=item.applied_rule_codes,
            )
            for item in context.controlled_reflection_experiment_comparisons
        )
