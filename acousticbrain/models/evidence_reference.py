from dataclasses import dataclass

from .evidence import EvidenceLevel


EvidenceValue = str | int | float | bool


@dataclass(frozen=True)
class EvidenceReference:
    """Référence stable vers un fait produit par une analyse structurée."""

    code: str
    source_analysis: str
    fact_code: str
    evidence_level: EvidenceLevel
    value: EvidenceValue | None = None

