from dataclasses import dataclass

from .energy_window_analysis import EnergyWindowAnalysis


@dataclass(frozen=True)
class DirectReverberantBandAnalysis:
    """Énergies directe et réverbérée factuelles d'une bande."""

    center_frequency_hz: float
    direct_window: EnergyWindowAnalysis
    early_window: EnergyWindowAnalysis
    late_window: EnergyWindowAnalysis
    total_window: EnergyWindowAnalysis
    direct_to_reverberant_db: float | None
    confidence: float
    method: str

    def __post_init__(self):
        self._validate_windows()
        self._validate_ratio()

    def _validate_windows(self):
        if self.direct_window.end_ms is None or self.early_window.end_ms is None:
            raise ValueError("Direct and early windows require finite ends.")
        if self.direct_window.end_ms > self.early_window.start_ms:
            raise ValueError("Direct and early windows cannot overlap.")
        if self.early_window.end_ms > self.late_window.start_ms:
            raise ValueError("Early and late windows cannot overlap.")
        if self.total_window.start_ms > self.direct_window.start_ms:
            raise ValueError("Total window must contain the direct window.")
        if (
            self.total_window.end_ms is not None
            and (
                self.late_window.end_ms is None
                or self.total_window.end_ms < self.late_window.end_ms
            )
        ):
            raise ValueError("Total window must contain the late window.")

    def _validate_ratio(self):
        if self.direct_to_reverberant_db is None:
            return
        direct = self.direct_window.energy
        early = self.early_window.energy
        late = self.late_window.energy
        if (
            direct is None
            or direct <= 0
            or early is None
            or late is None
            or early + late <= 0
        ):
            raise ValueError(
                "D/R requires exploitable direct, early and late energies."
            )
