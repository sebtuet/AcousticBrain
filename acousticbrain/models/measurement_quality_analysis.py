from dataclasses import dataclass

from .measurement_channel_quality import MeasurementChannelQuality
from .measurement_set_quality import MeasurementSetQuality


@dataclass(frozen=True)
class MeasurementQualityAnalysis:
    """Regroupe les faits de qualité sans décider de leur exploitabilité."""

    channel_qualities: tuple[MeasurementChannelQuality, ...] = ()
    measurement_set_quality: MeasurementSetQuality | None = None
    confidence: float = 0.0
    source_analyses: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.channel_qualities, tuple) or not isinstance(
            self.source_analyses, tuple
        ):
            raise ValueError("Measurement-quality collections must be tuples.")
        if self.measurement_set_quality is not None and not isinstance(
            self.measurement_set_quality, MeasurementSetQuality
        ):
            raise ValueError(
                "Measurement-quality set facts require MeasurementSetQuality."
            )
        channels = tuple(item.channel for item in self.channel_qualities)
        if len(channels) != len(set(channels)):
            raise ValueError("Measurement channel qualities must be unique.")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Measurement-quality confidence must be between 0 and 100.")
        if len(self.source_analyses) != len(set(self.source_analyses)) or any(
            not isinstance(source, str) or not source.strip()
            for source in self.source_analyses
        ):
            raise ValueError("Source analyses must be non-empty and unique.")
