from dataclasses import dataclass, field

from .clarity_band_analysis import ClarityBandAnalysis
from .impulse_channel import ImpulseChannel


@dataclass
class ClarityChannelAnalysis:
    """Agrégation des indicateurs de clarté pour un canal."""

    channel: ImpulseChannel
    band_analyses: list[ClarityBandAnalysis] = field(default_factory=list)
    broadband_c50_db: float | None = None
    broadband_c80_db: float | None = None
    broadband_d50_percent: float | None = None
    broadband_ts_s: float | None = None
    confidence: float = 0.0

