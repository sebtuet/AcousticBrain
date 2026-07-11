from dataclasses import dataclass, field

from .confidence_factor import ConfidenceFactor


@dataclass
class ConfidenceAnalysis:
    """Confiance agrégée et facteurs factuels qui la composent."""

    score: float = 0.0
    factors: list[ConfidenceFactor] = field(default_factory=list)
    available_evidence_count: int = 0
    missing_evidence_count: int = 0
    agreement_score: float = 0.0
    coverage_score: float = 0.0
