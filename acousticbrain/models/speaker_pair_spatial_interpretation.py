from dataclasses import dataclass

from .spatial_interpretation_status import (
    SpatialAlignmentStatus,
    SpatialBalanceStatus,
    SpatialCoherenceStatus,
    SpatialStabilityStatus,
)
from .spatial_measurement_type import SpatialMeasurementType


@dataclass(frozen=True)
class SpeakerPairSpatialInterpretation:
    """Interprétation technique d'une paire d'enceintes mesurée."""

    measurement_type: SpatialMeasurementType
    broadband_level_difference_db: float | None
    broadband_time_difference_ms: float | None
    broadband_cross_correlation: float | None
    level_symmetry: SpatialBalanceStatus
    relative_time_alignment: SpatialAlignmentStatus
    pair_coherence: SpatialCoherenceStatus
    technical_center_stability: SpatialStabilityStatus
    most_asymmetric_center_frequencies_hz: tuple[float, ...]
    confidence: float
    source_analysis: str = "SpatialAnalysis"

    def __post_init__(self):
        if self.measurement_type is not SpatialMeasurementType.SPEAKER_CHANNEL_PAIR:
            raise ValueError(
                "Speaker pair interpretation requires a speaker channel pair."
            )
