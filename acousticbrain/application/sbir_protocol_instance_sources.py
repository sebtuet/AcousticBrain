from dataclasses import dataclass

from acousticbrain.models import (
    EvidenceAcquisitionPlan,
    ExperimentDescriptor,
    GeometrySBIRCandidate,
    LoudspeakerPositioningExperimentProposal,
    SBIRProtocolInstanceInput,
)

from .evidence_plan_preparation import evidence_acquisition_plan_fingerprint


@dataclass(frozen=True)
class SBIRPlanSource:
    plan_id: str
    contract_fingerprint: str
    status: str


@dataclass(frozen=True)
class SBIRExperimentSource:
    experiment_id: str
    experiment_type: str
    state: str


@dataclass(frozen=True)
class SBIRGeometrySource:
    geometry_candidate_id: str
    speaker_id: str
    surface_id: str


@dataclass(frozen=True)
class SBIRDisplacementSource:
    proposal_id: str
    geometry_candidate_id: str | None
    surface_id: str | None
    displacement_m: float


@dataclass(frozen=True)
class SBIRProtocolInstanceSourceOverview:
    protocol_id: str
    plans: tuple[SBIRPlanSource, ...]
    experiments: tuple[SBIRExperimentSource, ...]
    geometry_candidates: tuple[SBIRGeometrySource, ...]
    displacement_proposals: tuple[SBIRDisplacementSource, ...]
    selection_status: str = "NO_SELECTION_PERFORMED"
    causality_status: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        collections = (
            self.plans,
            self.experiments,
            self.geometry_candidates,
            self.displacement_proposals,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise TypeError("SBIR source-overview collections must be tuples.")
        if self.protocol_id != SBIRProtocolInstanceInput.PROTOCOL_ID:
            raise ValueError("SBIR source-overview protocol identity is invalid.")
        if self.selection_status != "NO_SELECTION_PERFORMED":
            raise ValueError("SBIR source overview cannot select an object.")
        if self.causality_status != "NOT_ESTABLISHED":
            raise ValueError("SBIR source overview cannot establish causality.")


class SBIRProtocolInstanceSourceOverviewService:
    """Lists exact existing SBIR sources without ranking or selecting them."""

    def build(self, *, plans, experiments, geometry_candidates, proposals):
        plans = self._typed(plans, EvidenceAcquisitionPlan, "plans")
        experiments = self._typed(
            experiments,
            ExperimentDescriptor,
            "experiments",
        )
        geometry_candidates = self._typed(
            geometry_candidates,
            GeometrySBIRCandidate,
            "geometry candidates",
        )
        proposals = self._typed(
            proposals,
            LoudspeakerPositioningExperimentProposal,
            "displacement proposals",
        )
        return SBIRProtocolInstanceSourceOverview(
            protocol_id=SBIRProtocolInstanceInput.PROTOCOL_ID,
            plans=tuple(sorted(
                (
                    SBIRPlanSource(
                        plan_id=value.plan_id,
                        contract_fingerprint=(
                            evidence_acquisition_plan_fingerprint(value)
                        ),
                        status=value.status.value,
                    )
                    for value in plans
                    if value.plan_id == SBIRProtocolInstanceInput.SOURCE_PLAN_ID
                ),
                key=lambda value: (value.plan_id, value.contract_fingerprint),
            )),
            experiments=tuple(sorted(
                (
                    SBIRExperimentSource(
                        experiment_id=value.experiment_id,
                        experiment_type=value.experiment_type.value,
                        state=value.state.value,
                    )
                    for value in experiments
                ),
                key=lambda value: value.experiment_id,
            )),
            geometry_candidates=tuple(sorted(
                (
                    SBIRGeometrySource(
                        geometry_candidate_id=value.candidate_id,
                        speaker_id=value.speaker_id,
                        surface_id=value.surface_id,
                    )
                    for value in geometry_candidates
                ),
                key=lambda value: value.geometry_candidate_id,
            )),
            displacement_proposals=tuple(sorted(
                (
                    SBIRDisplacementSource(
                        proposal_id=value.proposal_id,
                        geometry_candidate_id=(
                            value.source_geometry_candidate_id
                        ),
                        surface_id=value.source_surface_id,
                        displacement_m=value.step_distance_m,
                    )
                    for value in proposals
                ),
                key=lambda value: value.proposal_id,
            )),
        )

    @staticmethod
    def _typed(values, expected_type, label):
        if not isinstance(values, tuple) or any(
            not isinstance(value, expected_type) for value in values
        ):
            raise TypeError(f"SBIR source-overview {label} must be a typed tuple.")
        return values
