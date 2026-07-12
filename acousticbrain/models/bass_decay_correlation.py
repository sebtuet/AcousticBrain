from dataclasses import dataclass, field


@dataclass(frozen=True)
class BassDecayCorrelation:
    """Corrélation factuelle fondée sur des analyses déjà structurées."""

    code: str
    center_frequencies_hz: tuple[float, ...] = ()
    source_metrics: dict[str, float] = field(default_factory=dict)
    source_analyses: tuple[str, ...] = ()
    score: float = 0.0
    confidence: float = 0.0
    technical_basis_codes: tuple[str, ...] = ()

    def __post_init__(self):
        if not 0.0 <= self.score <= 100.0:
            raise ValueError("Correlation score must be between 0 and 100.")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Correlation confidence must be between 0 and 100.")
