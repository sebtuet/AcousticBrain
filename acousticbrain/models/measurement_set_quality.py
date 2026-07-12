from dataclasses import dataclass

from .impulse_channel import ImpulseChannel
from .measurement_quality_issue import (
    MeasurementQualityIssue,
    MeasurementQualityScope,
)


@dataclass(frozen=True)
class MeasurementSetQuality:
    """Faits de cohérence technique entre plusieurs canaux."""

    available_channels: tuple[ImpulseChannel, ...] = ()
    required_channels: tuple[ImpulseChannel, ...] = ()
    issues: tuple[MeasurementQualityIssue, ...] = ()
    confidence: float = 0.0
    source_ids: tuple[str, ...] = ()

    def __post_init__(self):
        if not all(
            isinstance(collection, tuple)
            for collection in (
                self.available_channels,
                self.required_channels,
                self.issues,
                self.source_ids,
            )
        ):
            raise ValueError("Measurement-set collections must be tuples.")
        if any(
            not isinstance(channel, ImpulseChannel)
            for channel in (*self.available_channels, *self.required_channels)
        ):
            raise ValueError("Measurement-set channels must be ImpulseChannel values.")
        if len(self.available_channels) != len(set(self.available_channels)):
            raise ValueError("Available channels must be unique.")
        if len(self.required_channels) != len(set(self.required_channels)):
            raise ValueError("Required channels must be unique.")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Measurement-set confidence must be between 0 and 100.")
        if len(self.source_ids) != len(set(self.source_ids)) or any(
            not isinstance(source, str) or not source.strip()
            for source in self.source_ids
        ):
            raise ValueError("Measurement-set source ids must be non-empty and unique.")
        if any(
            issue.scope is not MeasurementQualityScope.MEASUREMENT_SET
            for issue in self.issues
        ):
            raise ValueError("Measurement-set issues must target the full set.")
