from dataclasses import dataclass, field

from .recommendation_priority import RecommendationPriority


RecommendationParameter = str | int | float | bool


@dataclass
class Recommendation:
    """Action acoustique structurée déduite d'analyses physiques."""

    code: str
    action: str
    target: str
    priority: RecommendationPriority
    confidence: float
    source_analyses: tuple[str, ...]
    parameters: dict[str, RecommendationParameter] = field(default_factory=dict)
