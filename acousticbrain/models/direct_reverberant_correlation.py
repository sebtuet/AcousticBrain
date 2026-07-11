from dataclasses import dataclass, field


@dataclass(frozen=True)
class DirectReverberantCorrelation:
    """Corrélation factuelle fondée sur des analyses énergétiques existantes."""

    code: str
    center_frequencies_hz: tuple[float, ...] = ()
    source_metrics: dict[str, float] = field(default_factory=dict)
    source_analyses: tuple[str, ...] = ()
    score: float = 0.0
    confidence: float = 0.0
    technical_basis_codes: tuple[str, ...] = ()
