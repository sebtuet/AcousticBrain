from dataclasses import dataclass


@dataclass(frozen=True)
class ExplanationLink:
    """Lien structuré entre faits, preuves, corrélations et actions."""

    code: str
    fact_codes: tuple[str, ...]
    evidence_codes: tuple[str, ...]
    correlation_codes: tuple[str, ...] = ()
    recommendation_codes: tuple[str, ...] = ()
    hypothesis_codes: tuple[str, ...] = ()
    action_codes: tuple[str, ...] = ()
    protocol_codes: tuple[str, ...] = ()
    candidate_codes: tuple[str, ...] = ()
    verification_proposal_codes: tuple[str, ...] = ()
    experiment_declaration_codes: tuple[str, ...] = ()
    experiment_comparison_codes: tuple[str, ...] = ()
    hypothesis_status_update_codes: tuple[str, ...] = ()
    ranking_codes: tuple[str, ...] = ()
    recommended_candidate_codes: tuple[str, ...] = ()
    iteration_codes: tuple[str, ...] = ()
