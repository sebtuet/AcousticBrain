from dataclasses import dataclass

from .spatial_channel_pair_analysis import SpatialChannelPairAnalysis
from .spatial_measurement_type import SpatialMeasurementType


@dataclass
class SpatialAnalysis:
    """Connaissance spatiale disponible pour une paire de mesures."""

    pair_analysis: SpatialChannelPairAnalysis | None = None
    source_measurement_type: SpatialMeasurementType | None = None
    confidence: float = 0.0

    def __post_init__(self):
        if (
            self.pair_analysis is not None
            and self.source_measurement_type
            is not self.pair_analysis.measurement_type
        ):
            raise ValueError(
                "Spatial analysis source type must match its pair analysis."
            )
