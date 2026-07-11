from dataclasses import dataclass, field

from .global_domain_analysis import GlobalDomainAnalysis
from .global_correlation import GlobalCorrelation


@dataclass
class GlobalAnalysis:
    """Synthèse acoustique globale, structurée et indépendante du rendu."""

    score: float | None = None
    confidence: float | None = None
    domains: list[GlobalDomainAnalysis] = field(default_factory=list)
    correlations: list[GlobalCorrelation] = field(default_factory=list)
    priority_domains: tuple[str, ...] = ()
    source_analyses: tuple[str, ...] = ()
