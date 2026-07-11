from dataclasses import dataclass


@dataclass(frozen=True)
class ClarityBandAnalysis:
    """Indicateurs temporels factuels d'une bande fréquentielle."""

    center_frequency_hz: float
    c50_db: float | None
    c80_db: float | None
    d50_percent: float | None
    ts_s: float | None
    confidence: float
    method: str | None

