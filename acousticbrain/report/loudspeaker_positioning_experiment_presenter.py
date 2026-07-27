from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedLoudspeakerPositioningExperimentProposal:
    proposal_id: str
    source_recommendation_ids: tuple[str, ...]
    source_hypothesis_codes: tuple[str, ...]
    target: str
    movement_axis: str
    movement_direction: str
    step_distance_m: float
    tested_variable: str
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    expected_observables: tuple[str, ...]
    rationale: tuple[str, ...]
    confidence: float
    causality_status: str
    proposal_status: str
    provenance: tuple[tuple[str, str], ...]
    source_surface_id: str | None = None
    source_geometry_candidate_id: str | None = None
    source_surface_role: str | None = None
    source_observation_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PresentedLoudspeakerPositioningExperimentAnalysis:
    proposal: PresentedLoudspeakerPositioningExperimentProposal | None
    proposal_status: str
    blocking_reason_codes: tuple[str, ...]
    considered_source_ids: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]


class LoudspeakerPositioningExperimentPresenter:
    """Projette le résultat PR-044 sans modifier sa sélection."""

    def present(self, context):
        analysis = context.loudspeaker_positioning_experiment_analysis
        if analysis is None:
            return None
        proposal = analysis.proposal
        return PresentedLoudspeakerPositioningExperimentAnalysis(
            proposal=(
                PresentedLoudspeakerPositioningExperimentProposal(
                    proposal_id=proposal.proposal_id,
                    source_recommendation_ids=proposal.source_recommendation_ids,
                    source_hypothesis_codes=proposal.source_hypothesis_codes,
                    target=proposal.target.value,
                    movement_axis=proposal.movement_axis.value,
                    movement_direction=proposal.movement_direction.value,
                    step_distance_m=proposal.step_distance_m,
                    tested_variable=proposal.tested_variable,
                    controlled_variables=proposal.controlled_variables,
                    required_measurements=proposal.required_measurements,
                    expected_observables=proposal.expected_observables,
                    rationale=proposal.rationale,
                    confidence=proposal.confidence,
                    causality_status=proposal.causality_status,
                    proposal_status=proposal.proposal_status.value,
                    provenance=proposal.provenance,
                    source_surface_id=proposal.source_surface_id,
                    source_geometry_candidate_id=(
                        proposal.source_geometry_candidate_id
                    ),
                    source_surface_role=(
                        proposal.source_surface_role.value
                        if proposal.source_surface_role is not None else None
                    ),
                    source_observation_ids=proposal.source_observation_ids,
                )
                if proposal is not None else None
            ),
            proposal_status=analysis.proposal_status.value,
            blocking_reason_codes=analysis.blocking_reason_codes,
            considered_source_ids=analysis.considered_source_ids,
            applied_rule_codes=analysis.applied_rule_codes,
        )
