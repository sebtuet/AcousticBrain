from dataclasses import dataclass

from .spatial_measurement_type import SpatialMeasurementType


@dataclass(frozen=True)
class SpatialBandAnalysis:
    """Faits de paire mesurés dans une bande fréquentielle."""

    center_frequency_hz: float
    level_difference_db: float | None
    time_difference_ms: float | None
    cross_correlation: float | None
    correlation_delay_ms: float | None
    interaural_level_difference_db: float | None
    interaural_time_difference_ms: float | None
    iacc: float | None
    measurement_type: SpatialMeasurementType
    confidence: float
    method: str

    def __post_init__(self):
        if self.measurement_type is SpatialMeasurementType.SPEAKER_CHANNEL_PAIR:
            interaural_values = (
                self.interaural_level_difference_db,
                self.interaural_time_difference_ms,
                self.iacc,
            )
            if any(value is not None for value in interaural_values):
                raise ValueError(
                    "Interaural metrics require a binaural measurement pair."
                )
