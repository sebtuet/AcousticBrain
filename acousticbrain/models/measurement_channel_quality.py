from dataclasses import dataclass
from math import isfinite

from .impulse_channel import ImpulseChannel
from .measurement_quality_issue import (
    MeasurementQualityIssue,
    MeasurementQualityScope,
)


@dataclass(frozen=True)
class MeasurementChannelQuality:
    """Faits techniques de qualité disponibles pour un canal."""

    channel: ImpulseChannel
    issues: tuple[MeasurementQualityIssue, ...] = ()
    sample_rate_hz: float | None = None
    sample_count: int | None = None
    duration_seconds: float | None = None
    direct_peak_index: int | None = None
    confidence: float = 0.0
    source_id: str | None = None

    def __post_init__(self):
        if not isinstance(self.channel, ImpulseChannel):
            raise ValueError("Channel quality requires an ImpulseChannel.")
        if not isinstance(self.issues, tuple):
            raise ValueError("Channel quality issues must be a tuple.")
        if self.sample_rate_hz is not None and (
            not isfinite(self.sample_rate_hz) or self.sample_rate_hz <= 0.0
        ):
            raise ValueError("Sample rate must be positive and finite.")
        if self.sample_count is not None and self.sample_count < 0:
            raise ValueError("Sample count cannot be negative.")
        if self.duration_seconds is not None and (
            not isfinite(self.duration_seconds) or self.duration_seconds < 0.0
        ):
            raise ValueError("Measurement duration must be finite and non-negative.")
        if self.direct_peak_index is not None and not isinstance(
            self.direct_peak_index, int
        ):
            raise ValueError("Direct-peak index must be an integer.")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Channel confidence must be between 0 and 100.")
        if self.source_id is not None and (
            not isinstance(self.source_id, str) or not self.source_id.strip()
        ):
            raise ValueError("Channel source id cannot be empty.")
        if any(
            issue.scope is not MeasurementQualityScope.CHANNEL
            or issue.channel is not self.channel
            for issue in self.issues
        ):
            raise ValueError("Channel issues must target their owning channel.")
