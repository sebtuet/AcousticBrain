from dataclasses import dataclass, field

from acousticbrain.models import EvidenceLevel


@dataclass
class Diagnostic:

    title: str

    message: str

    severity: str

    confidence: int

    evidence_level: EvidenceLevel

    causes: list[str] = field(default_factory=list)

    recommendations: list[str] = field(default_factory=list)