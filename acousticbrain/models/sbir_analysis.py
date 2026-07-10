from dataclasses import dataclass

from .reflection_surface import ReflectionSurface
from .sbir_candidate import SBIRCandidate


@dataclass
class SBIRAnalysis:
    candidates: list[SBIRCandidate]
    best_match: SBIRCandidate | None
    reflection_surface: ReflectionSurface | None
    reflection_distance_m: float | None
    delay_ms: float | None
    confidence: float
    score: float
