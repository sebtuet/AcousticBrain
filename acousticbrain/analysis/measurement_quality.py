from math import isfinite, log10, sqrt

from acousticbrain.models import (
    ImpulseResponse,
    MeasurementChannelQuality,
    MeasurementQualityIssue,
    MeasurementQualityIssueCode,
    MeasurementQualityScope,
    MeasurementQualityTechnicalSeverity,
)


class MeasurementQualityAnalyzer:
    """Établit des faits de qualité à partir d'une seule réponse impulsionnelle."""

    CLIPPING_ABSOLUTE_LEVEL = 0.999
    MINIMUM_CLIPPED_SAMPLE_COUNT = 2
    MINIMUM_DIRECT_PEAK_LEVEL = 0.01
    DIRECT_PEAK_GLOBAL_RATIO = 0.90
    HIGH_NOISE_FLOOR_DBFS = -40.0
    MINIMUM_DYNAMIC_RANGE_DB = 35.0
    MINIMUM_USEFUL_DURATION_SECONDS = 0.2
    MINIMUM_NOISE_SAMPLE_COUNT = 20
    NOISE_TAIL_FRACTION = 0.10
    SAMPLE_INTERVAL_RELATIVE_TOLERANCE = 1e-6
    TIMING_TOLERANCE_SAMPLES = 1.0
    PEAK_VALUE_RELATIVE_TOLERANCE = 1e-3
    SOURCE_ANALYSIS = "MeasurementQualityAnalyzer"

    def analyze(
        self,
        impulse_response: ImpulseResponse,
    ) -> MeasurementChannelQuality:
        if not isinstance(impulse_response, ImpulseResponse):
            raise TypeError("MeasurementQualityAnalyzer requires ImpulseResponse.")

        samples = tuple(
            float(value)
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            else float("nan")
            for value in impulse_response.samples
        )
        source_id = impulse_response.source_id or (
            f"impulse:{impulse_response.channel.value}"
        )
        issues = []
        sample_count = len(samples)
        sample_rate = (
            float(impulse_response.sample_rate_hz)
            if isinstance(impulse_response.sample_rate_hz, (int, float))
            and not isinstance(impulse_response.sample_rate_hz, bool)
            and isfinite(impulse_response.sample_rate_hz)
            and impulse_response.sample_rate_hz > 0.0
            else None
        )
        finite_samples = all(isfinite(value) for value in samples)
        absolute = tuple(abs(value) for value in samples) if finite_samples else ()
        global_peak = max(absolute, default=0.0)

        clipped_count = sum(
            value >= self.CLIPPING_ABSOLUTE_LEVEL for value in absolute
        )
        if clipped_count >= self.MINIMUM_CLIPPED_SAMPLE_COUNT:
            issues.append(
                self._issue(
                    MeasurementQualityIssueCode.CLIPPING_DETECTED,
                    impulse_response,
                    source_id,
                    observed={
                        "clipped_sample_count": clipped_count,
                        "maximum_absolute_level": global_peak,
                    },
                    thresholds={
                        "absolute_level": self.CLIPPING_ABSOLUTE_LEVEL,
                        "minimum_sample_count": self.MINIMUM_CLIPPED_SAMPLE_COUNT,
                    },
                    confidence=100.0,
                    severity=MeasurementQualityTechnicalSeverity.ERROR,
                )
            )

        if finite_samples and global_peak < self.MINIMUM_DIRECT_PEAK_LEVEL:
            issues.append(
                self._issue(
                    MeasurementQualityIssueCode.LOW_SIGNAL_LEVEL,
                    impulse_response,
                    source_id,
                    observed={"maximum_absolute_level": global_peak},
                    thresholds={
                        "minimum_direct_peak_level": (
                            self.MINIMUM_DIRECT_PEAK_LEVEL
                        )
                    },
                    confidence=100.0,
                    severity=MeasurementQualityTechnicalSeverity.WARNING,
                )
            )

        peak_index = impulse_response.peak_index
        peak_is_valid = self._credible_peak(
            peak_index,
            absolute,
            global_peak,
        )
        if not peak_is_valid:
            observed = {
                "sample_count": sample_count,
                "global_peak_index": (
                    absolute.index(global_peak) if absolute else -1
                ),
                "maximum_absolute_level": global_peak,
            }
            if peak_index is not None:
                observed["declared_peak_index"] = peak_index
            issues.append(
                self._issue(
                    MeasurementQualityIssueCode.INVALID_DIRECT_PEAK,
                    impulse_response,
                    source_id,
                    observed=observed,
                    thresholds={
                        "minimum_global_peak_ratio": (
                            self.DIRECT_PEAK_GLOBAL_RATIO
                        )
                    },
                    confidence=100.0,
                    severity=MeasurementQualityTechnicalSeverity.ERROR,
                )
            )

        noise_rms = self._noise_rms(samples) if finite_samples else None
        noise_floor_dbfs = self._dbfs(noise_rms)
        dynamic_range_db = self._dynamic_range(global_peak, noise_rms)
        if (
            noise_floor_dbfs is not None
            and noise_floor_dbfs > self.HIGH_NOISE_FLOOR_DBFS
        ):
            issues.append(
                self._issue(
                    MeasurementQualityIssueCode.HIGH_NOISE_FLOOR,
                    impulse_response,
                    source_id,
                    observed={
                        "noise_rms": noise_rms,
                        "noise_floor_dbfs": noise_floor_dbfs,
                    },
                    thresholds={
                        "maximum_noise_floor_dbfs": self.HIGH_NOISE_FLOOR_DBFS
                    },
                    confidence=self._noise_confidence(sample_count),
                    severity=MeasurementQualityTechnicalSeverity.WARNING,
                )
            )
        if (
            dynamic_range_db is not None
            and dynamic_range_db < self.MINIMUM_DYNAMIC_RANGE_DB
        ):
            issues.append(
                self._issue(
                    MeasurementQualityIssueCode.INSUFFICIENT_DYNAMIC_RANGE,
                    impulse_response,
                    source_id,
                    observed={"dynamic_range_db": dynamic_range_db},
                    thresholds={
                        "minimum_dynamic_range_db": self.MINIMUM_DYNAMIC_RANGE_DB
                    },
                    confidence=self._noise_confidence(sample_count),
                    severity=MeasurementQualityTechnicalSeverity.WARNING,
                )
            )

        useful_duration = (
            (sample_count - peak_index - 1) / sample_rate
            if peak_is_valid and sample_rate is not None
            else None
        )
        if (
            useful_duration is not None
            and useful_duration < self.MINIMUM_USEFUL_DURATION_SECONDS
        ):
            issues.append(
                self._issue(
                    MeasurementQualityIssueCode.INSUFFICIENT_IR_DURATION,
                    impulse_response,
                    source_id,
                    observed={"useful_duration_seconds": useful_duration},
                    thresholds={
                        "minimum_useful_duration_seconds": (
                            self.MINIMUM_USEFUL_DURATION_SECONDS
                        )
                    },
                    confidence=100.0,
                    severity=MeasurementQualityTechnicalSeverity.ERROR,
                )
            )

        metadata_metrics = self._metadata_inconsistencies(
            impulse_response,
            samples,
            sample_rate,
            peak_is_valid,
        )
        if metadata_metrics:
            issues.append(
                self._issue(
                    MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA,
                    impulse_response,
                    source_id,
                    observed=metadata_metrics,
                    thresholds={
                        "sample_interval_relative_tolerance": (
                            self.SAMPLE_INTERVAL_RELATIVE_TOLERANCE
                        ),
                        "timing_tolerance_samples": self.TIMING_TOLERANCE_SAMPLES,
                        "peak_value_relative_tolerance": (
                            self.PEAK_VALUE_RELATIVE_TOLERANCE
                        ),
                    },
                    confidence=100.0,
                    severity=MeasurementQualityTechnicalSeverity.ERROR,
                )
            )

        return MeasurementChannelQuality(
            channel=impulse_response.channel,
            issues=tuple(self._ordered(issues)),
            sample_rate_hz=sample_rate,
            sample_count=sample_count,
            duration_seconds=(
                sample_count / sample_rate if sample_rate is not None else None
            ),
            direct_peak_index=peak_index,
            confidence=self._confidence(
                sample_count=sample_count,
                sample_rate_available=sample_rate is not None,
                finite_samples=finite_samples,
                peak_is_valid=peak_is_valid,
                noise_available=noise_rms is not None,
            ),
            source_id=source_id,
        )

    @classmethod
    def _credible_peak(cls, peak_index, absolute, global_peak):
        return (
            isinstance(peak_index, int)
            and not isinstance(peak_index, bool)
            and 0 <= peak_index < len(absolute)
            and global_peak > 0.0
            and absolute[peak_index] >= cls.DIRECT_PEAK_GLOBAL_RATIO * global_peak
        )

    @classmethod
    def _noise_rms(cls, samples):
        if not samples:
            return None
        tail_count = max(
            cls.MINIMUM_NOISE_SAMPLE_COUNT,
            round(len(samples) * cls.NOISE_TAIL_FRACTION),
        )
        if len(samples) < tail_count:
            return None
        tail = samples[-tail_count:]
        return sqrt(sum(value * value for value in tail) / len(tail))

    @staticmethod
    def _dbfs(value):
        if value is None:
            return None
        if value <= 0.0:
            return -300.0
        return 20.0 * log10(value)

    @staticmethod
    def _dynamic_range(peak, noise):
        if noise is None or peak <= 0.0:
            return None
        if noise <= 0.0:
            return 300.0
        return 20.0 * log10(peak / noise)

    @classmethod
    def _noise_confidence(cls, sample_count):
        required = cls.MINIMUM_NOISE_SAMPLE_COUNT / cls.NOISE_TAIL_FRACTION
        return 100.0 * min(1.0, sample_count / required)

    @classmethod
    def _metadata_inconsistencies(
        cls,
        impulse_response,
        samples,
        sample_rate,
        peak_is_valid,
    ):
        metrics = {}
        if not all(isfinite(value) for value in samples):
            metrics["non_finite_sample_count"] = sum(
                not isfinite(value) for value in samples
            )
        if sample_rate is None:
            metrics["invalid_sample_rate"] = True
        if (
            impulse_response.response_length is not None
            and impulse_response.response_length != len(samples)
        ):
            metrics["declared_response_length"] = impulse_response.response_length
            metrics["observed_sample_count"] = len(samples)
        if impulse_response.sample_interval_s is not None:
            interval = impulse_response.sample_interval_s
            if (
                isinstance(interval, bool)
                or not isinstance(interval, (int, float))
                or not isfinite(interval)
                or interval <= 0.0
            ):
                metrics["invalid_sample_interval"] = True
            elif sample_rate is not None:
                expected = 1.0 / sample_rate
                relative_error = abs(interval - expected) / expected
                if relative_error > cls.SAMPLE_INTERVAL_RELATIVE_TOLERANCE:
                    metrics["sample_interval_relative_error"] = relative_error
        timing_values = (
            impulse_response.start_time_s,
            impulse_response.time_offset_seconds,
        )
        if any(
            value is not None
            and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
            )
            for value in timing_values
        ):
            metrics["invalid_timing_metadata"] = True
        elif sample_rate is not None and impulse_response.start_time_s is not None:
            timing_error_samples = abs(
                impulse_response.start_time_s
                - impulse_response.time_offset_seconds
            ) * sample_rate
            if timing_error_samples > cls.TIMING_TOLERANCE_SAMPLES:
                metrics["start_offset_error_samples"] = timing_error_samples
        if impulse_response.peak_value is not None and (
            isinstance(impulse_response.peak_value, bool)
            or not isinstance(impulse_response.peak_value, (int, float))
            or not isfinite(impulse_response.peak_value)
        ):
            metrics["invalid_peak_value"] = True
        elif peak_is_valid and impulse_response.peak_value is not None:
            observed_peak = samples[impulse_response.peak_index]
            denominator = max(abs(observed_peak), 1e-12)
            relative_error = abs(
                impulse_response.peak_value - observed_peak
            ) / denominator
            if relative_error > cls.PEAK_VALUE_RELATIVE_TOLERANCE:
                metrics["peak_value_relative_error"] = relative_error
        return metrics

    @staticmethod
    def _confidence(
        *,
        sample_count,
        sample_rate_available,
        finite_samples,
        peak_is_valid,
        noise_available,
    ):
        checks = (
            sample_count > 0,
            sample_rate_available,
            finite_samples,
            peak_is_valid,
            noise_available,
        )
        return 100.0 * sum(checks) / len(checks)

    @staticmethod
    def _issue(
        code,
        impulse_response,
        source_id,
        *,
        observed,
        thresholds,
        confidence,
        severity,
    ):
        return MeasurementQualityIssue(
            code=code,
            scope=MeasurementQualityScope.CHANNEL,
            channel=impulse_response.channel,
            observed_metrics=observed,
            applied_thresholds=thresholds,
            confidence=confidence,
            severity=severity,
            source_ids=(source_id,),
        )

    @staticmethod
    def _ordered(issues):
        order = {
            code: index for index, code in enumerate(MeasurementQualityIssueCode)
        }
        return sorted(issues, key=lambda item: order[item.code])
