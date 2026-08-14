from dataclasses import dataclass, field

from .impulse_channel import ImpulseChannel
from .rt60_band_analysis import RT60BandAnalysis


@dataclass
class RT60ChannelAnalysis:
    """Agrégation des résultats RT60 d'un canal."""

    channel: ImpulseChannel
    band_analyses: list[RT60BandAnalysis] = field(default_factory=list)
    broadband_rt60_seconds: float | None = None
    minimum_rt60_seconds: float | None = None
    maximum_rt60_seconds: float | None = None
    confidence: float = 0.0

