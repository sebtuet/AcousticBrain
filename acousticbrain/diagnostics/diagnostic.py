from dataclasses import dataclass, field

from acousticbrain.models import EvidenceLevel


@dataclass
class Diagnostic:

    title: str

    message: str

    severity: str

    confidence: int

    evidence_level: EvidenceLevel

    score: float | None = None

    observations: list[str] = field(default_factory=list)

    conclusion: str | None = None

    causes: list[str] = field(default_factory=list)

    recommendations: list[str] = field(default_factory=list)

    analysis_family: str | None = None

    readiness_status: str | None = None

    provisional: bool = False

    validity: str | None = None

    score_label: str = "Score"
