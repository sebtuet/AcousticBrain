from statistics import fmean

from acousticbrain.models import (
    ImpulseChannel,
    MeasurementChannelQuality,
    MeasurementQualityIssue,
    MeasurementQualityIssueCode,
    MeasurementQualityScope,
    MeasurementQualityTechnicalSeverity,
    MeasurementSetQuality,
)


class MeasurementSetQualityAnalyzer:
    """Établit les faits de cohérence entre qualités mono-canal existantes."""

    DEFAULT_REQUIRED_CHANNELS = (
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
        ImpulseChannel.STEREO,
    )
    SAMPLE_RATE_TOLERANCE_HZ = 0.0
    LENGTH_RELATIVE_TOLERANCE = 0.01
    TIMING_TOLERANCE_SECONDS = 0.001
    SOURCE_ANALYSIS = "MeasurementSetQualityAnalyzer"

    def analyze(
        self,
        channel_qualities: dict[
            ImpulseChannel, MeasurementChannelQuality
        ],
        *,
        required_channels: tuple[ImpulseChannel, ...] | None = None,
    ) -> MeasurementSetQuality:
        self._validate(channel_qualities)
        required = (
            self.DEFAULT_REQUIRED_CHANNELS
            if required_channels is None
            else required_channels
        )
        if not isinstance(required, tuple) or any(
            not isinstance(channel, ImpulseChannel) for channel in required
        ):
            raise ValueError("Required channels must be an ImpulseChannel tuple.")
        if len(required) != len(set(required)):
            raise ValueError("Required channels must be unique.")

        available = tuple(
            channel for channel in ImpulseChannel if channel in channel_qualities
        )
        qualities = [channel_qualities[channel] for channel in available]
        raw_source_ids = tuple(
            quality.source_id or f"channel:{quality.channel.value}"
            for quality in qualities
        )
        source_ids = tuple(dict.fromkeys(raw_source_ids))
        duplicate_source_id_count = len(raw_source_ids) - len(source_ids)
        set_source_ids = source_ids or ("measurement-set",)
        issues = []

        for channel in required:
            if channel not in channel_qualities:
                issues.append(
                    self._issue(
                        MeasurementQualityIssueCode.MISSING_REQUIRED_CHANNEL,
                        set_source_ids,
                        observed={"missing_channel": channel.value},
                        thresholds={"required_channel_count": len(required)},
                        severity=MeasurementQualityTechnicalSeverity.ERROR,
                    )
                )

        rates = {
            quality.channel: quality.sample_rate_hz
            for quality in qualities
            if quality.sample_rate_hz is not None
        }
        if len(set(rates.values())) > 1:
            issues.append(
                self._issue(
                    MeasurementQualityIssueCode.CHANNEL_SAMPLE_RATE_MISMATCH,
                    set_source_ids,
                    observed={
                        "minimum_sample_rate_hz": min(rates.values()),
                        "maximum_sample_rate_hz": max(rates.values()),
                        "compared_channel_count": len(rates),
                    },
                    thresholds={
                        "sample_rate_tolerance_hz": self.SAMPLE_RATE_TOLERANCE_HZ
                    },
                    severity=MeasurementQualityTechnicalSeverity.ERROR,
                )
            )

        lengths = {
            quality.channel: quality.sample_count
            for quality in qualities
            if quality.sample_count is not None
        }
        if len(lengths) >= 2:
            maximum_length = max(lengths.values())
            relative_spread = (
                (maximum_length - min(lengths.values())) / maximum_length
                if maximum_length > 0
                else 0.0
            )
            if relative_spread > self.LENGTH_RELATIVE_TOLERANCE:
                issues.append(
                    self._issue(
                        MeasurementQualityIssueCode.CHANNEL_LENGTH_MISMATCH,
                        set_source_ids,
                        observed={
                            "minimum_sample_count": min(lengths.values()),
                            "maximum_sample_count": maximum_length,
                            "relative_length_spread": relative_spread,
                        },
                        thresholds={
                            "maximum_relative_length_spread": (
                                self.LENGTH_RELATIVE_TOLERANCE
                            )
                        },
                        severity=MeasurementQualityTechnicalSeverity.WARNING,
                    )
                )

        peak_times = {
            quality.channel: quality.direct_peak_index / quality.sample_rate_hz
            for quality in qualities
            if quality.direct_peak_index is not None
            and quality.direct_peak_index >= 0
            and (
                quality.sample_count is None
                or quality.direct_peak_index < quality.sample_count
            )
            and quality.sample_rate_hz is not None
            and all(
                issue.code is not MeasurementQualityIssueCode.INVALID_DIRECT_PEAK
                for issue in quality.issues
            )
        }
        if len(peak_times) >= 2:
            timing_spread = max(peak_times.values()) - min(peak_times.values())
            if timing_spread > self.TIMING_TOLERANCE_SECONDS:
                issues.append(
                    self._issue(
                        MeasurementQualityIssueCode.CHANNEL_TIMING_MISMATCH,
                        set_source_ids,
                        observed={
                            "minimum_direct_peak_time_s": min(
                                peak_times.values()
                            ),
                            "maximum_direct_peak_time_s": max(
                                peak_times.values()
                            ),
                            "direct_peak_time_spread_s": timing_spread,
                        },
                        thresholds={
                            "maximum_timing_spread_s": (
                                self.TIMING_TOLERANCE_SECONDS
                            )
                        },
                        severity=MeasurementQualityTechnicalSeverity.ERROR,
                    )
                )

        metadata_channels = tuple(
            quality.channel
            for quality in qualities
            if quality.sample_rate_hz is None
            or any(
                issue.code
                is MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA
                for issue in quality.issues
            )
        )
        if metadata_channels or duplicate_source_id_count:
            observed = {
                "inconsistent_channel_count": len(metadata_channels),
                "inconsistent_channels": ",".join(
                    channel.value for channel in metadata_channels
                ),
            }
            if duplicate_source_id_count:
                observed["duplicate_source_id_count"] = (
                    duplicate_source_id_count
                )
            issues.append(
                self._issue(
                    MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA,
                    set_source_ids,
                    observed=observed,
                    thresholds={},
                    severity=MeasurementQualityTechnicalSeverity.ERROR,
                )
            )

        coverage = (
            sum(channel in channel_qualities for channel in required)
            / len(required)
            if required
            else 1.0
        )
        local_confidence = (
            fmean(quality.confidence for quality in qualities)
            if qualities
            else 0.0
        )
        return MeasurementSetQuality(
            available_channels=available,
            required_channels=required,
            issues=tuple(self._ordered(issues)),
            confidence=local_confidence * coverage,
            source_ids=source_ids,
        )

    @staticmethod
    def _validate(channel_qualities):
        if not isinstance(channel_qualities, dict):
            raise TypeError("Channel qualities must be provided as a dict.")
        for channel, quality in channel_qualities.items():
            if not isinstance(quality, MeasurementChannelQuality):
                raise TypeError("MeasurementChannelQuality values are required.")
            if channel is not quality.channel:
                raise ValueError(
                    "Measurement channel quality does not match its channel key."
                )

    @staticmethod
    def _issue(code, source_ids, *, observed, thresholds, severity):
        return MeasurementQualityIssue(
            code=code,
            scope=MeasurementQualityScope.MEASUREMENT_SET,
            observed_metrics=observed,
            applied_thresholds=thresholds,
            confidence=100.0,
            severity=severity,
            source_ids=source_ids,
        )

    @staticmethod
    def _ordered(issues):
        order = {
            code: index for index, code in enumerate(MeasurementQualityIssueCode)
        }
        return sorted(issues, key=lambda item: order[item.code])
