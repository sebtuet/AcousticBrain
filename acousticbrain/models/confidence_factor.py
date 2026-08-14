from dataclasses import dataclass


@dataclass
class ConfidenceFactor:
    """Contribution factuelle d'une source de preuve à la confiance globale."""

    source: str
    score: float
    weight: float
    available: bool
    explanation: str
