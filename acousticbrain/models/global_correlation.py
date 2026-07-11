from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalCorrelation:
    """Lien factuel entre plusieurs domaines d'analyse."""

    code: str
    domain_codes: tuple[str, ...]
    source_analyses: tuple[str, ...]
    score: float

