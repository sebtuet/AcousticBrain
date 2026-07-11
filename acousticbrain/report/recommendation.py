from dataclasses import dataclass, field

from acousticbrain.models import RecommendationParameter, RecommendationPriority


@dataclass(frozen=True)
class PresentedRecommendation:
    """Projection structurée d'une recommandation pour les consommateurs."""

    code: str
    action: str
    target: str
    priority: RecommendationPriority
    confidence: float
    source_analyses: tuple[str, ...]
    parameters: dict[str, RecommendationParameter] = field(default_factory=dict)


class RecommendationPresenter:
    """Projette le résultat existant sans l'interpréter ni le recalculer."""

    def present(self, context) -> list[PresentedRecommendation]:
        analysis = context.recommendation_analysis
        if analysis is None:
            return []

        return [
            PresentedRecommendation(
                code=recommendation.code,
                action=recommendation.action,
                target=recommendation.target,
                priority=recommendation.priority,
                confidence=recommendation.confidence,
                source_analyses=recommendation.source_analyses,
                parameters=dict(recommendation.parameters),
            )
            for recommendation in analysis.recommendations
        ]

