from dataclasses import dataclass
from enum import Enum


class GlobalDomainKind(Enum):
    ACOUSTIC = "ACOUSTIC"
    MEASUREMENT_QUALITY = "MEASUREMENT_QUALITY"


@dataclass(frozen=True)
class GlobalDomainAnalysis:
    """Contribution structurée d'un domaine à la synthèse globale."""

    code: str
    score: float
    confidence: float | None
    source_analysis: str
    recommendation_codes: tuple[str, ...] = ()
    kind: GlobalDomainKind = GlobalDomainKind.ACOUSTIC

    @property
    def contributes_to_acoustic_score(self) -> bool:
        return self.kind is GlobalDomainKind.ACOUSTIC
