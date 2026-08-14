from dataclasses import FrozenInstanceError
from math import inf

import pytest

from acousticbrain.models import (
    ImpulseChannel,
    MeasurementChannelQuality,
    MeasurementQualityAnalysis,
    MeasurementQualityIssue,
    MeasurementQualityIssueCode,
    MeasurementQualityScope,
    MeasurementQualityTechnicalSeverity,
    MeasurementSetQuality,
)


def channel_issue(channel=ImpulseChannel.LEFT):
    return MeasurementQualityIssue(
        code=MeasurementQualityIssueCode.CLIPPING_DETECTED,
        scope=MeasurementQualityScope.CHANNEL,
        channel=channel,
        observed_metrics={"clipped_sample_count": 12, "peak_level": 1.0},
        applied_thresholds={"absolute_peak_limit": 0.999},
        confidence=98.0,
        severity=MeasurementQualityTechnicalSeverity.ERROR,
        source_ids=("impulse-left",),
    )


def set_issue():
    return MeasurementQualityIssue(
        code=MeasurementQualityIssueCode.CHANNEL_SAMPLE_RATE_MISMATCH,
        scope=MeasurementQualityScope.MEASUREMENT_SET,
        observed_metrics={
            "left_sample_rate_hz": 48000.0,
            "right_sample_rate_hz": 44100.0,
        },
        applied_thresholds={"sample_rate_tolerance_hz": 0.0},
        confidence=100.0,
        severity=MeasurementQualityTechnicalSeverity.ERROR,
        source_ids=("impulse-left", "impulse-right"),
    )


def test_issue_codes_are_stable_and_complete_for_pr021a():
    assert {item.value for item in MeasurementQualityIssueCode} == {
        "CLIPPING_DETECTED",
        "LOW_SIGNAL_LEVEL",
        "HIGH_NOISE_FLOOR",
        "INSUFFICIENT_DYNAMIC_RANGE",
        "INVALID_DIRECT_PEAK",
        "INSUFFICIENT_IR_DURATION",
        "CHANNEL_SAMPLE_RATE_MISMATCH",
        "CHANNEL_LENGTH_MISMATCH",
        "CHANNEL_TIMING_MISMATCH",
        "MISSING_REQUIRED_CHANNEL",
        "INCONSISTENT_MEASUREMENT_METADATA",
    }


def test_channel_issue_keeps_metrics_thresholds_confidence_and_provenance():
    issue = channel_issue()

    assert issue.channel is ImpulseChannel.LEFT
    assert issue.observed_metrics["clipped_sample_count"] == 12
    assert issue.applied_thresholds["absolute_peak_limit"] == 0.999
    assert issue.confidence == 98.0
    assert issue.severity is MeasurementQualityTechnicalSeverity.ERROR
    assert issue.source_ids == ("impulse-left",)
    with pytest.raises(TypeError):
        issue.observed_metrics["new"] = 1
    with pytest.raises(FrozenInstanceError):
        issue.confidence = 0.0


def test_issue_scope_and_channel_must_be_consistent():
    with pytest.raises(ValueError, match="requires"):
        MeasurementQualityIssue(
            code=MeasurementQualityIssueCode.LOW_SIGNAL_LEVEL,
            scope=MeasurementQualityScope.CHANNEL,
            source_ids=("source",),
        )
    with pytest.raises(ValueError, match="cannot target"):
        MeasurementQualityIssue(
            code=MeasurementQualityIssueCode.MISSING_REQUIRED_CHANNEL,
            scope=MeasurementQualityScope.MEASUREMENT_SET,
            channel=ImpulseChannel.LEFT,
            source_ids=("set",),
        )


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"confidence": 101.0}, "confidence"),
        ({"source_ids": ()}, "provenance"),
        ({"applied_thresholds": {"limit": inf}}, "thresholds"),
        ({"observed_metrics": {"peak": inf}}, "metrics"),
    ],
)
def test_issue_rejects_invalid_technical_facts(changes, message):
    values = channel_issue().__dict__ | changes
    values["observed_metrics"] = dict(values["observed_metrics"])
    values["applied_thresholds"] = dict(values["applied_thresholds"])

    with pytest.raises(ValueError, match=message):
        MeasurementQualityIssue(**values)


def test_channel_quality_keeps_unavailable_facts_as_none():
    quality = MeasurementChannelQuality(channel=ImpulseChannel.SUB)

    assert quality.sample_rate_hz is None
    assert quality.sample_count is None
    assert quality.duration_seconds is None
    assert quality.direct_peak_index is None
    assert quality.issues == ()
    assert not hasattr(quality, "score")


def test_channel_quality_accepts_only_issues_for_its_channel():
    with pytest.raises(ValueError, match="owning channel"):
        MeasurementChannelQuality(
            channel=ImpulseChannel.RIGHT,
            issues=(channel_issue(ImpulseChannel.LEFT),),
        )


def test_measurement_set_quality_keeps_cross_channel_facts():
    quality = MeasurementSetQuality(
        available_channels=(ImpulseChannel.LEFT, ImpulseChannel.RIGHT),
        required_channels=(
            ImpulseChannel.LEFT,
            ImpulseChannel.RIGHT,
            ImpulseChannel.STEREO,
        ),
        issues=(set_issue(),),
        confidence=92.0,
        source_ids=("impulse-left", "impulse-right"),
    )

    assert quality.issues[0].scope is MeasurementQualityScope.MEASUREMENT_SET
    assert quality.required_channels[-1] is ImpulseChannel.STEREO
    assert not hasattr(quality, "is_usable")


def test_analysis_groups_unique_channel_and_set_facts_without_policy():
    left = MeasurementChannelQuality(
        channel=ImpulseChannel.LEFT,
        issues=(channel_issue(),),
        sample_rate_hz=48000.0,
        sample_count=48000,
        duration_seconds=1.0,
        direct_peak_index=100,
        confidence=95.0,
        source_id="impulse-left",
    )
    set_quality = MeasurementSetQuality(
        available_channels=(ImpulseChannel.LEFT,),
        issues=(
            MeasurementQualityIssue(
                code=MeasurementQualityIssueCode.MISSING_REQUIRED_CHANNEL,
                scope=MeasurementQualityScope.MEASUREMENT_SET,
                observed_metrics={"missing_channel": "RIGHT"},
                confidence=100.0,
                source_ids=("measurement-set",),
            ),
        ),
    )

    analysis = MeasurementQualityAnalysis(
        channel_qualities=(left,),
        measurement_set_quality=set_quality,
        confidence=94.0,
        source_analyses=(
            "MeasurementQualityAnalyzer",
            "MeasurementSetQualityAnalyzer",
        ),
    )

    assert analysis.channel_qualities == (left,)
    assert analysis.measurement_set_quality is set_quality
    assert not hasattr(analysis, "readiness")
    assert not hasattr(analysis, "recommendations")


def test_analysis_rejects_duplicate_channel_qualities():
    left = MeasurementChannelQuality(channel=ImpulseChannel.LEFT)

    with pytest.raises(ValueError, match="unique"):
        MeasurementQualityAnalysis(channel_qualities=(left, left))


def test_contract_rejects_mutable_collections():
    with pytest.raises(ValueError, match="tuple"):
        MeasurementChannelQuality(
            channel=ImpulseChannel.LEFT,
            issues=[channel_issue()],
        )
    with pytest.raises(ValueError, match="tuples"):
        MeasurementSetQuality(available_channels=[ImpulseChannel.LEFT])
    with pytest.raises(ValueError, match="tuples"):
        MeasurementQualityAnalysis(channel_qualities=[])
