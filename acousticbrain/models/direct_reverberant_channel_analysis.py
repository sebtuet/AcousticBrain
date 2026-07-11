from dataclasses import dataclass, field

from .direct_reverberant_band_analysis import DirectReverberantBandAnalysis
from .energy_window_analysis import EnergyWindowAnalysis
from .impulse_channel import ImpulseChannel


@dataclass
class DirectReverberantChannelAnalysis:
    """Agrégation D/R par bande et large bande pour un canal."""

    channel: ImpulseChannel
    band_analyses: list[DirectReverberantBandAnalysis] = field(
        default_factory=list
    )
    broadband_direct_window: EnergyWindowAnalysis | None = None
    broadband_early_window: EnergyWindowAnalysis | None = None
    broadband_late_window: EnergyWindowAnalysis | None = None
    broadband_total_window: EnergyWindowAnalysis | None = None
    broadband_direct_to_reverberant_db: float | None = None
    window_start_ms: float = 0.0
    direct_end_ms: float = 0.0
    early_end_ms: float = 0.0
    analysis_end_ms: float | None = None
    confidence: float = 0.0
    method: str = ""

    def __post_init__(self):
        if not self.window_start_ms <= self.direct_end_ms <= self.early_end_ms:
            raise ValueError("Configured energy window bounds must be ordered.")
        if (
            self.analysis_end_ms is not None
            and self.analysis_end_ms < self.early_end_ms
        ):
            raise ValueError("Analysis end must follow the early window.")
        if self.broadband_direct_to_reverberant_db is not None:
            self._validate_broadband_ratio()

    def _validate_broadband_ratio(self):
        windows = (
            self.broadband_direct_window,
            self.broadband_early_window,
            self.broadband_late_window,
        )
        if any(window is None or window.energy is None for window in windows):
            raise ValueError("Broadband D/R requires all component energies.")
        direct, early, late = (window.energy for window in windows)
        if direct <= 0 or early + late <= 0:
            raise ValueError("Broadband D/R energies must be exploitable.")
