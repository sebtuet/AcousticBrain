from dataclasses import dataclass


@dataclass
class RT60BandAnalysis:
    """Résultat RT60 structuré pour une bande fréquentielle."""

    center_frequency_hz: float
    minimum_frequency_hz: float
    maximum_frequency_hz: float
    rt60_seconds: float | None
    decay_range_db: tuple[float, float]
    fit_correlation: float | None
    confidence: float
    edt_seconds: float | None = None
    t20_seconds: float | None = None
    t30_seconds: float | None = None
    selected_estimate: str | None = None
    noise_floor_db: float | None = None
