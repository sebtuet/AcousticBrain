from dataclasses import dataclass, field

from .recommendation import Recommendation


@dataclass
class RecommendationAnalysis:
    """Résultat structuré du futur moteur de recommandation."""

    recommendations: list[Recommendation] = field(default_factory=list)

