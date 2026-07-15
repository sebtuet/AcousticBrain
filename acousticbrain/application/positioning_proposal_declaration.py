from acousticbrain.models import ExperimentKind

from .experiment_declaration import ExperimentDeclarationService


class PositioningProposalDeclarationService:
    """Convertit une proposition PR-044 acceptée en déclaration PR-043."""

    def __init__(self, declaration_service=None):
        self.declaration_service = (
            declaration_service or ExperimentDeclarationService()
        )

    def declare(
        self,
        measurement_root,
        *,
        experiment_code,
        reference_experiment_code,
        proposal,
        user_note=None,
    ):
        if proposal.causality_status != "NOT_ESTABLISHED":
            raise ValueError("An accepted positioning proposal cannot establish causality.")
        if proposal.tested_variable != "LOUDSPEAKER_POSITION":
            raise ValueError("Only a loudspeaker-positioning proposal can be accepted.")
        provenance = f"USER_ACCEPTED_POSITIONING_PROPOSAL:{proposal.proposal_id}"
        return self.declaration_service.declare(
            measurement_root,
            experiment_code=experiment_code,
            experiment_kind=ExperimentKind.CONTROLLED_INTERVENTION,
            reference_experiment_code=reference_experiment_code,
            modified_variables=(proposal.tested_variable,),
            controlled_variables=proposal.controlled_variables,
            user_note=user_note,
            provenance_source=provenance,
        )
