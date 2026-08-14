from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedReflectionCandidateVerificationProposal:
    proposal_id: str
    source_candidate_id: str
    proposal_order: int
    correlation_id: str
    path_id: str
    surface_id: str
    region_id: str | None
    observed_event_id: str
    target_kind: str
    target_id: str
    method: str
    reference_condition_code: str
    intervention_condition_code: str
    controlled_variable_codes: tuple[str, ...]
    changed_variable_codes: tuple[str, ...]
    observable_fact_codes: tuple[str, ...]
    supporting_outcome_codes: tuple[str, ...]
    counter_outcome_codes: tuple[str, ...]
    source_evidence_codes: tuple[str, ...]
    source_provenance_codes: tuple[str, ...]
    planning_rule_codes: tuple[str, ...]
    execution_status: str
    causality_status: str
    eligibility_impact: str
    recommendation_impact: str
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class PresentedReflectionCandidateVerificationExclusion:
    source_candidate_id: str
    reason: str
    source_evidence_codes: tuple[str, ...]
    source_provenance_codes: tuple[str, ...]


@dataclass(frozen=True)
class PresentedControlledReflectionVerificationPlanningAnalysis:
    proposals: tuple[PresentedReflectionCandidateVerificationProposal, ...]
    exclusions: tuple[PresentedReflectionCandidateVerificationExclusion, ...]
    source_analysis_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]


class ControlledReflectionVerificationPlanningPresenter:
    """Projects descriptive proposals without resolving or executing them."""

    def present(self, context):
        analysis = context.controlled_reflection_verification_planning_analysis
        if analysis is None or (not analysis.proposals and not analysis.exclusions):
            return None
        return PresentedControlledReflectionVerificationPlanningAnalysis(
            proposals=tuple(
                PresentedReflectionCandidateVerificationProposal(
                    proposal_id=item.proposal_id,
                    source_candidate_id=item.source_candidate_id,
                    proposal_order=item.proposal_order,
                    correlation_id=item.correlation_id,
                    path_id=item.path_id,
                    surface_id=item.surface_id,
                    region_id=item.region_id,
                    observed_event_id=item.observed_event_id,
                    target_kind=item.target_kind,
                    target_id=item.target_id,
                    method=item.method.value,
                    reference_condition_code=item.reference_condition_code,
                    intervention_condition_code=item.intervention_condition_code,
                    controlled_variable_codes=item.controlled_variable_codes,
                    changed_variable_codes=item.changed_variable_codes,
                    observable_fact_codes=item.observable_fact_codes,
                    supporting_outcome_codes=item.supporting_outcome_codes,
                    counter_outcome_codes=item.counter_outcome_codes,
                    source_evidence_codes=item.source_evidence_codes,
                    source_provenance_codes=item.source_provenance_codes,
                    planning_rule_codes=item.planning_rule_codes,
                    execution_status=item.execution_status.value,
                    causality_status=item.causality_status.value,
                    eligibility_impact=item.eligibility_impact.value,
                    recommendation_impact=item.recommendation_impact.value,
                    limitations=item.limitations,
                )
                for item in analysis.proposals
            ),
            exclusions=tuple(
                PresentedReflectionCandidateVerificationExclusion(
                    source_candidate_id=item.source_candidate_id,
                    reason=item.reason.value,
                    source_evidence_codes=item.source_evidence_codes,
                    source_provenance_codes=item.source_provenance_codes,
                )
                for item in analysis.exclusions
            ),
            source_analysis_codes=analysis.source_analysis_codes,
            applied_rule_codes=analysis.applied_rule_codes,
        )
