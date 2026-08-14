from dataclasses import dataclass


@dataclass(frozen=True)
class EnergyWindowAnalysis:
    """Énergie factuelle intégrée entre deux bornes temporelles explicites."""

    name: str
    start_ms: float
    end_ms: float | None
    energy: float | None
    relative_energy_db: float | None
    confidence: float
    method: str

    def __post_init__(self):
        if self.end_ms is not None and self.end_ms <= self.start_ms:
            raise ValueError("Energy window end must be after its start.")
        if self.energy is not None and self.energy < 0:
            raise ValueError("Energy window energy cannot be negative.")
        if self.relative_energy_db is not None and self.energy is None:
            raise ValueError(
                "Relative energy requires an available window energy."
            )
