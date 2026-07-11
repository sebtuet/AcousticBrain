from dataclasses import dataclass


@dataclass(frozen=True)
class ExplanationLink:
    """Lien structuré entre faits, preuves, corrélations et actions."""

    code: str
    fact_codes: tuple[str, ...]
    evidence_codes: tuple[str, ...]
    correlation_codes: tuple[str, ...] = ()
    recommendation_codes: tuple[str, ...] = ()
