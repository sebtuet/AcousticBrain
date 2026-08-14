from dataclasses import dataclass, field

from .spatial_band_analysis import SpatialBandAnalysis
from .spatial_measurement_type import SpatialMeasurementType


@dataclass
class SpatialChannelPairAnalysis:
    """Agrégation des faits spatiaux calculés pour une paire de signaux."""

    measurement_type: SpatialMeasurementType
    bands: list[SpatialBandAnalysis] = field(default_factory=list)
    broadband_level_difference_db: float | None = None
    broadband_time_difference_ms: float | None = None
    broadband_cross_correlation: float | None = None
    confidence: float = 0.0
    method: str = ""

    def __post_init__(self):
        if any(
            band.measurement_type is not self.measurement_type
            for band in self.bands
        ):
            raise ValueError(
                "Spatial bands must use the channel pair measurement type."
            )
