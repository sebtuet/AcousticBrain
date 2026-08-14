from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Mapping

from .reasoning_codes import VerificationActionType
from .recommendation import RecommendationParameter
from .recommendation_priority import RecommendationPriority


@dataclass(frozen=True)
class VerificationAction:
    code: str
    action_type: VerificationActionType
    target: str
    priority: RecommendationPriority
    confidence: float
    evidence_fact_codes: tuple[str, ...]
    expected_supporting_fact_codes: tuple[str, ...]
    expected_counter_fact_codes: tuple[str, ...]
    parameters: Mapping[str, RecommendationParameter] = field(default_factory=dict)
    definitive: bool = False

    def __post_init__(self):
        if not isinstance(self.code, str) or not self.code.strip():
            raise ValueError("Verification-action code is required.")
        if not isinstance(self.action_type, VerificationActionType):
            raise ValueError("Verification-action type is invalid.")
        if not isinstance(self.target, str) or not self.target.strip():
            raise ValueError("Verification-action target is required.")
        if not isinstance(self.priority, RecommendationPriority):
            raise ValueError("Verification-action priority is invalid.")
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Verification-action confidence must be bounded.")
        for collection in (
            self.evidence_fact_codes,
            self.expected_supporting_fact_codes,
            self.expected_counter_fact_codes,
        ):
            if not isinstance(collection, tuple):
                raise ValueError("Verification-action facts must be tuples.")
            if len(collection) != len(set(collection)):
                raise ValueError("Verification-action facts must be unique.")
        if not self.evidence_fact_codes:
            raise ValueError("Verification actions require supporting provenance.")
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
