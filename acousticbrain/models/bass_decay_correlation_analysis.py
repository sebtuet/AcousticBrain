from dataclasses import dataclass, field

from .bass_decay_correlation import BassDecayCorrelation


@dataclass
class BassDecayCorrelationAnalysis:
    """Ensemble structuré des corrélations Bass Decay."""

    correlations: list[BassDecayCorrelation] = field(default_factory=list)
    source_analyses: tuple[str, ...] = ()
    confidence: float = 0.0

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Correlation confidence must be between 0 and 100.")
