from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalDomainAnalysis:
    """Contribution structurée d'un domaine à la synthèse globale."""

    code: str
    score: float
    confidence: float | None
    source_analysis: str
    recommendation_codes: tuple[str, ...] = ()

