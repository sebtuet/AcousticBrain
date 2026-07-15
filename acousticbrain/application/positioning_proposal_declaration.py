from dataclasses import dataclass

from acousticbrain.models import ExperimentKind

from .experiment_declaration import ExperimentDeclarationService


@dataclass(frozen=True)
class PositioningProposalDeclarationDraft:
    proposal_id: str
    experiment_kind: ExperimentKind
    reference_experiment_code: str
    modified_variables: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    user_note: str | None
    field_provenance: tuple[tuple[str, str], ...]


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
        draft = self.build_draft(
            proposal=proposal,
            reference_experiment_code=reference_experiment_code,
            user_note=user_note,
        )
        self.declaration_service.declare(
            measurement_root,
            experiment_code=experiment_code,
            experiment_kind=draft.experiment_kind,
            reference_experiment_code=draft.reference_experiment_code,
            modified_variables=draft.modified_variables,
            controlled_variables=draft.controlled_variables,
            user_note=draft.user_note,
            provenance_source=dict(draft.field_provenance)["experiment_kind"],
        )
        return draft

    @staticmethod
    def build_draft(*, proposal, reference_experiment_code, user_note=None):
        if proposal.causality_status != "NOT_ESTABLISHED":
            raise ValueError("An accepted positioning proposal cannot establish causality.")
        if proposal.tested_variable != "LOUDSPEAKER_POSITION":
            raise ValueError("Only a loudspeaker-positioning proposal can be accepted.")
        if not isinstance(reference_experiment_code, str) or not reference_experiment_code.strip():
            raise ValueError("A positioning declaration draft requires a reference experiment.")
        provenance = f"USER_ACCEPTED_POSITIONING_PROPOSAL:{proposal.proposal_id}"
        return PositioningProposalDeclarationDraft(
            proposal_id=proposal.proposal_id,
            experiment_kind=ExperimentKind.CONTROLLED_INTERVENTION,
            reference_experiment_code=reference_experiment_code.strip(),
            modified_variables=(proposal.tested_variable,),
            controlled_variables=proposal.controlled_variables,
            user_note=user_note,
            field_provenance=tuple(
                (field, provenance)
                for field in ExperimentDeclarationService.DECLARATION_FIELDS
            ),
        )
