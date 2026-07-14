from dataclasses import dataclass, field
from enum import Enum

from .recommendation_priority import RecommendationPriority


RecommendationParameter = str | int | float | bool


class RecommendationStatus(Enum):
    ACTIVE = "ACTIVE"
    DEFERRED = "DEFERRED"
    COMPLETED = "COMPLETED"


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
    hypothesis_codes: tuple[str, ...] = ()
    verification_action: bool = False
    status: RecommendationStatus = RecommendationStatus.ACTIVE
    status_reason: str | None = None
