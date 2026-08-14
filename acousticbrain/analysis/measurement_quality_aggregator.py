from statistics import fmean

from acousticbrain.models import (
    ImpulseChannel,
    MeasurementChannelQuality,
    MeasurementQualityAnalysis,
    MeasurementSetQuality,
)


class MeasurementQualityAggregator:
    """Regroupe les faits mono-canal et multi-canaux sans politique."""

    SOURCE_ANALYSES = (
        "MeasurementQualityAnalyzer",
        "MeasurementSetQualityAnalyzer",
    )

    def aggregate(
        self,
        channel_qualities: dict[
            ImpulseChannel, MeasurementChannelQuality
        ],
        measurement_set_quality: MeasurementSetQuality,
    ) -> MeasurementQualityAnalysis:
        if not isinstance(measurement_set_quality, MeasurementSetQuality):
            raise TypeError("MeasurementSetQuality is required.")
        for channel, quality in channel_qualities.items():
            if channel is not quality.channel:
                raise ValueError(
                    "Measurement channel quality does not match its channel key."
                )
        qualities = tuple(
            channel_qualities[channel]
            for channel in ImpulseChannel
            if channel in channel_qualities
        )
        confidences = (
            *(quality.confidence for quality in qualities),
            measurement_set_quality.confidence,
        )
        return MeasurementQualityAnalysis(
            channel_qualities=qualities,
            measurement_set_quality=measurement_set_quality,
            confidence=fmean(confidences) if confidences else 0.0,
            source_analyses=self.SOURCE_ANALYSES,
        )
