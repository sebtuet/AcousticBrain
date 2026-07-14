from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedRoomDescriptionChangeProposal:
    proposal_id: str
    status: str
    target_kind: str | None
    target_id: str | None
    requested_changes: tuple[str, ...]
    interpreted_facts: tuple[str, ...]
    unresolved_ambiguities: tuple[str, ...]
    validation_issues: tuple[str, ...]
    completeness_before: float
    completeness_after: float
    potentially_unblocked_capabilities: tuple[str, ...]
    eligibility_disclaimer: str
    requires_confirmation: bool


class RoomDescriptionChangeProposalPresenter:
    """Résumé factuel avant confirmation, sans reformulation LLM."""

    def present(self, proposal):
        return PresentedRoomDescriptionChangeProposal(
            proposal_id=proposal.proposal_id,
            status=proposal.status.value,
            target_kind=proposal.target_kind,
            target_id=proposal.target_id,
            requested_changes=tuple(
                f"{item.change_kind.value}:{item.target_kind}:{item.target_id}:"
                f"{item.value_id}:{item.catalog_entry_id}"
                for item in proposal.requested_changes
            ),
            interpreted_facts=tuple(
                f"{item.fact_code}={item.value}@{item.confidence:g}"
                for item in proposal.interpreted_facts
            ),
            unresolved_ambiguities=proposal.unresolved_ambiguities,
            validation_issues=tuple(
                f"{item.code}:{item.field}" for item in proposal.validation_issues
            ),
            completeness_before=proposal.predicted_completeness_change.before,
            completeness_after=proposal.predicted_completeness_change.after,
            potentially_unblocked_capabilities=(
                proposal.potentially_unblocked_capabilities
            ),
            eligibility_disclaimer=(
                "Projection informative only; eligibility requires a complete new analysis."
            ),
            requires_confirmation=proposal.requires_confirmation,
        )
