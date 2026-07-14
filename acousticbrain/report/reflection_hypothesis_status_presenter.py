from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedControlledReflectionHypothesisStatusUpdate:
    update_id: str
    target_kind: str
    target_id: str
    proposal_id: str
    experiment_declaration_id: str
    comparison_id: str | None
    status: str
    measured_fact_codes: tuple[str, ...]
    comparison_result_codes: tuple[str, ...]
    transition_rule_codes: tuple[str, ...]
    status_provenance_codes: tuple[str, ...]
    justification_codes: tuple[str, ...]
    causality_status: str
    recommendation_impact: str
    ranking_impact: str
    eligibility_impact: str
    source_analysis_codes: tuple[str, ...]


class ControlledReflectionHypothesisStatusPresenter:
    def present(self, context):
        return tuple(
            PresentedControlledReflectionHypothesisStatusUpdate(
                update_id=item.update_id,
                target_kind=item.target_kind,
                target_id=item.target_id,
                proposal_id=item.proposal_id,
                experiment_declaration_id=item.experiment_declaration_id,
                comparison_id=item.comparison_id,
                status=item.status.value,
                measured_fact_codes=item.measured_fact_codes,
                comparison_result_codes=item.comparison_result_codes,
                transition_rule_codes=item.transition_rule_codes,
                status_provenance_codes=item.status_provenance_codes,
                justification_codes=item.justification_codes,
                causality_status=item.causality_status.value,
                recommendation_impact=item.recommendation_impact.value,
                ranking_impact=item.ranking_impact.value,
                eligibility_impact=item.eligibility_impact.value,
                source_analysis_codes=item.source_analysis_codes,
            )
            for item in context.controlled_reflection_hypothesis_status_updates
        )
