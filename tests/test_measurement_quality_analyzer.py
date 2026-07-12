from copy import deepcopy

import pytest

from acousticbrain.analysis import MeasurementQualityAnalyzer
from acousticbrain.models import (
    ImpulseChannel,
    ImpulseResponse,
    MeasurementQualityIssueCode,
    MeasurementQualityScope,
)


def impulse(
    samples,
    *,
    sample_rate=1000.0,
    peak_index=10,
    **metadata,
):
    return ImpulseResponse(
        channel=ImpulseChannel.LEFT,
        sample_rate_hz=sample_rate,
        samples=list(samples),
        peak_index=peak_index,
        source_id="ir-left",
        **metadata,
    )


def clean_impulse():
    samples = [0.0] * 500
    samples[10] = 0.8
    return impulse(
        samples,
        response_length=500,
        sample_interval_s=0.001,
        start_time_s=0.0,
        time_offset_seconds=0.0,
        peak_value=0.8,
    )


def codes(result):
    return [issue.code for issue in result.issues]


def test_returns_factual_channel_quality_for_a_clean_impulse():
    result = MeasurementQualityAnalyzer().analyze(clean_impulse())

    assert result.channel is ImpulseChannel.LEFT
    assert result.issues == ()
    assert result.sample_rate_hz == 1000.0
    assert result.sample_count == 500
    assert result.duration_seconds == 0.5
    assert result.direct_peak_index == 10
    assert result.confidence == 100.0
    assert result.source_id == "ir-left"


def test_detects_repeated_full_scale_clipping_with_observed_thresholds():
    samples = [0.0] * 500
    samples[10:12] = [1.0, 1.0]

    result = MeasurementQualityAnalyzer().analyze(impulse(samples))
    issue = result.issues[0]

    assert issue.code is MeasurementQualityIssueCode.CLIPPING_DETECTED
    assert issue.scope is MeasurementQualityScope.CHANNEL
    assert issue.observed_metrics["clipped_sample_count"] == 2
    assert issue.applied_thresholds["absolute_level"] == 0.999
    assert issue.source_ids == ("ir-left",)


def test_one_normalized_direct_peak_is_not_called_clipping():
    samples = [0.0] * 500
    samples[10] = 1.0

    result = MeasurementQualityAnalyzer().analyze(impulse(samples))

    assert MeasurementQualityIssueCode.CLIPPING_DETECTED not in codes(result)


@pytest.mark.parametrize("peak_index", [None, -1, 500, 20])
def test_detects_missing_out_of_bounds_or_implausible_direct_peak(peak_index):
    samples = [0.0] * 500
    samples[10] = 0.8
    if peak_index == 20:
        samples[20] = 0.1

    result = MeasurementQualityAnalyzer().analyze(
        impulse(samples, peak_index=peak_index)
    )

    assert MeasurementQualityIssueCode.INVALID_DIRECT_PEAK in codes(result)
    assert result.direct_peak_index == peak_index


def test_detects_low_signal_and_insufficient_dynamic_range():
    samples = [0.005] * 500
    samples[10] = 0.009

    result = MeasurementQualityAnalyzer().analyze(impulse(samples))

    assert codes(result) == [
        MeasurementQualityIssueCode.LOW_SIGNAL_LEVEL,
        MeasurementQualityIssueCode.INSUFFICIENT_DYNAMIC_RANGE,
    ]
    dynamic = result.issues[1]
    assert dynamic.observed_metrics["dynamic_range_db"] < 35.0


def test_detects_high_noise_floor_and_insufficient_dynamic_range():
    samples = [0.02] * 500
    samples[10] = 0.8

    result = MeasurementQualityAnalyzer().analyze(impulse(samples))

    assert codes(result) == [
        MeasurementQualityIssueCode.HIGH_NOISE_FLOOR,
        MeasurementQualityIssueCode.INSUFFICIENT_DYNAMIC_RANGE,
    ]
    assert result.issues[0].observed_metrics["noise_floor_dbfs"] > -40.0


def test_detects_insufficient_useful_duration_after_the_direct_peak():
    samples = [0.0] * 100
    samples[10] = 0.8

    result = MeasurementQualityAnalyzer().analyze(impulse(samples))

    issue = next(
        item
        for item in result.issues
        if item.code is MeasurementQualityIssueCode.INSUFFICIENT_IR_DURATION
    )
    assert issue.observed_metrics["useful_duration_seconds"] == 0.089
    assert issue.applied_thresholds[
        "minimum_useful_duration_seconds"
    ] == 0.2


def test_detects_inconsistent_response_length_interval_timing_and_peak_value():
    source = clean_impulse()
    source.response_length = 499
    source.sample_interval_s = 0.002
    source.start_time_s = 0.01
    source.peak_value = 0.4

    result = MeasurementQualityAnalyzer().analyze(source)

    issue = next(
        item
        for item in result.issues
        if item.code
        is MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA
    )
    assert issue.observed_metrics["declared_response_length"] == 499
    assert issue.observed_metrics["observed_sample_count"] == 500
    assert issue.observed_metrics["sample_interval_relative_error"] == 1.0
    assert issue.observed_metrics["start_offset_error_samples"] == 10.0
    assert issue.observed_metrics["peak_value_relative_error"] == 0.5


def test_invalid_sample_rate_is_reported_without_creating_replacement_duration():
    source = clean_impulse()
    source.sample_rate_hz = 0.0

    result = MeasurementQualityAnalyzer().analyze(source)

    assert result.sample_rate_hz is None
    assert result.duration_seconds is None
    assert result.confidence == 80.0
    metadata = next(
        item
        for item in result.issues
        if item.code
        is MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA
    )
    assert metadata.observed_metrics["invalid_sample_rate"] is True


def test_non_finite_or_untyped_signal_metadata_is_reported_structurally():
    source = clean_impulse()
    source.samples[20] = "invalid"
    source.sample_interval_s = float("inf")
    source.start_time_s = float("nan")
    source.peak_value = "invalid"

    result = MeasurementQualityAnalyzer().analyze(source)

    metadata = next(
        item
        for item in result.issues
        if item.code
        is MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA
    )
    assert metadata.observed_metrics["non_finite_sample_count"] == 1
    assert metadata.observed_metrics["invalid_sample_interval"] is True
    assert metadata.observed_metrics["invalid_timing_metadata"] is True
    assert metadata.observed_metrics["invalid_peak_value"] is True
    assert result.confidence == 40.0


def test_analyzer_does_not_mutate_or_correct_the_impulse_response():
    source = clean_impulse()
    before = deepcopy(source)

    MeasurementQualityAnalyzer().analyze(source)

    assert source == before


def test_rejects_inputs_other_than_impulse_response():
    with pytest.raises(TypeError, match="ImpulseResponse"):
        MeasurementQualityAnalyzer().analyze(object())
