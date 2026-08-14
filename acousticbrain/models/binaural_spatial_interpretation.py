from dataclasses import dataclass, field

from .spatial_interpretation_status import (
    SpatialAlignmentStatus,
    SpatialBalanceStatus,
    SpatialCoherenceStatus,
)
from .spatial_measurement_type import SpatialMeasurementType


@dataclass(frozen=True)
class BinauralSpatialInterpretation:
    """Interprétation des métriques issues d'un protocole binaural."""

    measurement_type: SpatialMeasurementType
    interaural_level_differences_db: dict[float, float] = field(default_factory=dict)
    interaural_time_differences_ms: dict[float, float] = field(default_factory=dict)
    interaural_cross_correlations: dict[float, float] = field(default_factory=dict)
    interaural_level_balance: SpatialBalanceStatus = SpatialBalanceStatus.UNAVAILABLE
    interaural_time_alignment: SpatialAlignmentStatus = SpatialAlignmentStatus.UNAVAILABLE
    interaural_coherence: SpatialCoherenceStatus = SpatialCoherenceStatus.UNAVAILABLE
    confidence: float = 0.0
    source_analysis: str = "SpatialAnalysis"

    def __post_init__(self):
        if self.measurement_type is not SpatialMeasurementType.BINAURAL_PAIR:
            raise ValueError(
                "Binaural interpretation requires a binaural measurement pair."
            )
