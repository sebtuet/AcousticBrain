import inspect

import pytest

from acousticbrain.analysis import (
    AnalysisContext,
    MeasurementQualityAggregator,
    MeasurementSetQualityAnalyzer,
)
from acousticbrain.brain import pipeline
from acousticbrain.brain.stages.measurement_quality import MeasurementQualityStage
from acousticbrain.models import (
    ImpulseChannel,
    ImpulseResponse,
    Measurement,
    MeasurementChannelQuality,
    MeasurementQualityIssue,
    MeasurementQualityIssueCode,
    MeasurementQualityScope,
    MeasurementSetQuality,
    Room,
)
from acousticbrain.project import Project


def quality(
    channel,
    *,
    rate=48000.0,
    count=48000,
    peak=100,
    confidence=90.0,
    issues=(),
):
    return MeasurementChannelQuality(
        channel=channel,
        issues=issues,
        sample_rate_hz=rate,
        sample_count=count,
        duration_seconds=(count / rate if rate else None),
        direct_peak_index=peak,
        confidence=confidence,
        source_id=f"ir-{channel.value.lower()}",
    )


def codes(result):
    return [issue.code for issue in result.issues]


def test_accepts_a_coherent_required_measurement_set():
    qualities = {
        channel: quality(channel)
        for channel in (
            ImpulseChannel.LEFT,
            ImpulseChannel.RIGHT,
            ImpulseChannel.STEREO,
        )
    }

    result = MeasurementSetQualityAnalyzer().analyze(qualities)

    assert result.available_channels == (
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
        ImpulseChannel.STEREO,
    )
    assert result.required_channels == (
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
        ImpulseChannel.STEREO,
    )
    assert result.issues == ()
    assert result.confidence == 90.0


def test_reports_each_missing_required_channel_deterministically():
    result = MeasurementSetQualityAnalyzer().analyze(
        {ImpulseChannel.LEFT: quality(ImpulseChannel.LEFT)}
    )

    missing = [
        issue
        for issue in result.issues
        if issue.code is MeasurementQualityIssueCode.MISSING_REQUIRED_CHANNEL
    ]
    assert [item.observed_metrics["missing_channel"] for item in missing] == [
        "RIGHT",
        "STEREO",
    ]
    assert result.confidence == 30.0


def test_detects_sample_rate_length_and_direct_timing_mismatches():
    qualities = {
        ImpulseChannel.LEFT: quality(
            ImpulseChannel.LEFT,
            rate=48000.0,
            count=48000,
            peak=100,
        ),
        ImpulseChannel.RIGHT: quality(
            ImpulseChannel.RIGHT,
            rate=44100.0,
            count=47000,
            peak=200,
        ),
        ImpulseChannel.STEREO: quality(
            ImpulseChannel.STEREO,
            rate=48000.0,
            count=48000,
            peak=100,
        ),
    }

    result = MeasurementSetQualityAnalyzer().analyze(qualities)

    assert codes(result) == [
        MeasurementQualityIssueCode.CHANNEL_SAMPLE_RATE_MISMATCH,
        MeasurementQualityIssueCode.CHANNEL_LENGTH_MISMATCH,
        MeasurementQualityIssueCode.CHANNEL_TIMING_MISMATCH,
    ]
    assert result.issues[0].applied_thresholds[
        "sample_rate_tolerance_hz"
    ] == 0.0
    assert result.issues[1].applied_thresholds[
        "maximum_relative_length_spread"
    ] == 0.01
    assert result.issues[2].applied_thresholds[
        "maximum_timing_spread_s"
    ] == 0.001


def test_length_at_tolerance_and_timing_at_threshold_are_compatible():
    result = MeasurementSetQualityAnalyzer().analyze(
        {
            ImpulseChannel.LEFT: quality(
                ImpulseChannel.LEFT, count=1000, rate=1000.0, peak=10
            ),
            ImpulseChannel.RIGHT: quality(
                ImpulseChannel.RIGHT, count=990, rate=1000.0, peak=11
            ),
        },
        required_channels=(ImpulseChannel.LEFT, ImpulseChannel.RIGHT),
    )

    assert result.issues == ()


def test_lifts_channel_metadata_inconsistency_without_moving_original_issue():
    channel_issue = MeasurementQualityIssue(
        code=MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA,
        scope=MeasurementQualityScope.CHANNEL,
        channel=ImpulseChannel.LEFT,
        observed_metrics={"invalid_sample_rate": True},
        confidence=100.0,
        source_ids=("ir-left",),
    )
    left = quality(
        ImpulseChannel.LEFT,
        rate=None,
        issues=(channel_issue,),
    )

    result = MeasurementSetQualityAnalyzer().analyze(
        {ImpulseChannel.LEFT: left},
        required_channels=(ImpulseChannel.LEFT,),
    )

    issue = result.issues[0]
    assert issue.scope is MeasurementQualityScope.MEASUREMENT_SET
    assert issue.observed_metrics["inconsistent_channels"] == "LEFT"
    assert left.issues == (channel_issue,)


def test_duplicate_source_ids_become_metadata_issue_instead_of_exception():
    left = quality(ImpulseChannel.LEFT)
    right = quality(ImpulseChannel.RIGHT)
    object.__setattr__(right, "source_id", left.source_id)

    result = MeasurementSetQualityAnalyzer().analyze(
        {ImpulseChannel.LEFT: left, ImpulseChannel.RIGHT: right},
        required_channels=(ImpulseChannel.LEFT, ImpulseChannel.RIGHT),
    )

    issue = result.issues[0]
    assert issue.code is (
        MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA
    )
    assert issue.observed_metrics["duplicate_source_id_count"] == 1
    assert result.source_ids == ("ir-left",)


def test_refuses_a_channel_key_mismatch():
    with pytest.raises(ValueError, match="channel key"):
        MeasurementSetQualityAnalyzer().analyze(
            {ImpulseChannel.RIGHT: quality(ImpulseChannel.LEFT)}
        )


def test_aggregator_preserves_channel_facts_and_combines_technical_confidence():
    left = quality(ImpulseChannel.LEFT, confidence=90.0)
    right = quality(ImpulseChannel.RIGHT, confidence=80.0)
    set_quality = MeasurementSetQuality(
        available_channels=(ImpulseChannel.LEFT, ImpulseChannel.RIGHT),
        confidence=85.0,
    )

    result = MeasurementQualityAggregator().aggregate(
        {
            ImpulseChannel.RIGHT: right,
            ImpulseChannel.LEFT: left,
        },
        set_quality,
    )

    assert result.channel_qualities == (left, right)
    assert result.measurement_set_quality is set_quality
    assert result.confidence == 85.0
    assert result.source_analyses == (
        "MeasurementQualityAnalyzer",
        "MeasurementSetQualityAnalyzer",
    )


class RecordingChannelAnalyzer:
    def __init__(self):
        self.inputs = []

    def analyze(self, impulse_response):
        self.inputs.append(impulse_response)
        return quality(impulse_response.channel)


class RecordingSetAnalyzer:
    def __init__(self):
        self.input = None
        self.result = MeasurementSetQuality()

    def analyze(self, values):
        self.input = values
        return self.result


class RecordingAggregator:
    def __init__(self):
        self.inputs = None
        self.result = object()

    def aggregate(self, *inputs):
        self.inputs = inputs
        return self.result


def test_stage_analyzes_each_impulse_and_stores_only_the_aggregation():
    project = Project("Project", Room("Room", 5.0, 4.0, 2.5))
    left = ImpulseResponse(ImpulseChannel.LEFT, 48000.0, [1.0])
    right = ImpulseResponse(ImpulseChannel.RIGHT, 48000.0, [1.0])
    project.add_impulse_response(left)
    project.add_impulse_response(right)
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    channel_analyzer = RecordingChannelAnalyzer()
    set_analyzer = RecordingSetAnalyzer()
    aggregator = RecordingAggregator()

    MeasurementQualityStage(
        channel_analyzer,
        set_analyzer,
        aggregator,
    ).run(project, context)

    assert channel_analyzer.inputs == [left, right]
    assert set(set_analyzer.input) == {
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
    }
    assert aggregator.inputs == (set_analyzer.input, set_analyzer.result)
    assert context.measurement_quality_analysis is aggregator.result


def test_pipeline_places_quality_stage_before_physics_and_temporal_analysis():
    source = inspect.getsource(pipeline.BrainPipeline.run)

    quality = source.index("MeasurementQualityStage().run")
    assert quality < source.index("PhysicsStage().run")
    assert quality < source.index("TemporalAnalysisStage().run")
