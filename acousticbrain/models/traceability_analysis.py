from dataclasses import dataclass, field

from .evidence_reference import EvidenceReference
from .explanation_link import ExplanationLink


@dataclass
class TraceabilityAnalysis:
    """Graphe de traçabilité structuré produit par le futur moteur."""

    evidence_references: list[EvidenceReference] = field(default_factory=list)
    links: list[ExplanationLink] = field(default_factory=list)
    source_analyses: tuple[str, ...] = ()
