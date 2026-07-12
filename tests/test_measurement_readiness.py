import inspect

import pytest

from acousticbrain.analysis import AnalysisContext, MeasurementReadinessEngine
from acousticbrain.brain import pipeline
from acousticbrain.brain.stages.measurement_readiness import (
    MeasurementReadinessStage,
)
from acousticbrain.models import (
    AnalysisReadiness,
    ImpulseChannel,
    Measurement,
    MeasurementAnalysisFamily,
    MeasurementChannelQuality,
    MeasurementQualityAnalysis,
    MeasurementQualityIssue,
    MeasurementQualityIssueCode,
    MeasurementQualityScope,
    MeasurementReadinessAnalysis,
    MeasurementReadinessStatus,
    MeasurementSetQuality,
)


def issue(code, *, channel=None, metric=None):
    scope = (
        MeasurementQualityScope.CHANNEL
        if channel is not None
        else MeasurementQualityScope.MEASUREMENT_SET
    )
    return MeasurementQualityIssue(
        code=code,
        scope=scope,
        channel=channel,
        observed_metrics=metric or {},
        confidence=90.0,
        source_ids=(
            f"ir-{channel.value.lower()}" if channel else "measurement-set",
        ),
    )


def channel_quality(channel, issues=(), confidence=90.0):
    return MeasurementChannelQuality(
        channel=channel,
        issues=issues,
        sample_rate_hz=48000.0,
        sample_count=48000,
        duration_seconds=1.0,
        direct_peak_index=100,
        confidence=confidence,
        source_id=f"ir-{channel.value.lower()}",
    )


def quality_analysis(channel_qualities, set_issues=(), confidence=90.0):
    qualities = tuple(channel_qualities)
    return MeasurementQualityAnalysis(
        channel_qualities=qualities,
        measurement_set_quality=MeasurementSetQuality(
            available_channels=tuple(item.channel for item in qualities),
            issues=set_issues,
            confidence=confidence,
        ),
        confidence=confidence,
        source_analyses=(
            "MeasurementQualityAnalyzer",
            "MeasurementSetQualityAnalyzer",
        ),
    )


def by_family(result):
    return {item.family: item for item in result.analyses}


def clean_quality():
    return quality_analysis(
        channel_quality(channel)
        for channel in (
            ImpulseChannel.LEFT,
            ImpulseChannel.RIGHT,
            ImpulseChannel.STEREO,
        )
    )


def test_clean_measurement_is_available_for_every_family():
    result = MeasurementReadinessEngine().analyze(clean_quality())

    assert tuple(item.family for item in result.analyses) == tuple(
        MeasurementAnalysisFamily
    )
    assert all(
        item.status is MeasurementReadinessStatus.AVAILABLE
        for item in result.analyses
    )
    assert result.confidence == 90.0


def test_one_invalid_channel_becomes_reservation_when_another_is_eligible():
    invalid_peak = issue(
        MeasurementQualityIssueCode.INVALID_DIRECT_PEAK,
        channel=ImpulseChannel.LEFT,
    )
    quality = quality_analysis(
        (
            channel_quality(ImpulseChannel.LEFT, (invalid_peak,)),
            channel_quality(ImpulseChannel.RIGHT),
            channel_quality(ImpulseChannel.STEREO),
        )
    )

    decisions = by_family(MeasurementReadinessEngine().analyze(quality))

    assert decisions[MeasurementAnalysisFamily.RT60].status is (
        MeasurementReadinessStatus.AVAILABLE_WITH_RESERVATIONS
    )
    assert decisions[MeasurementAnalysisFamily.RT60].blocking_issues == ()
    assert decisions[MeasurementAnalysisFamily.RT60].non_blocking_issues == (
        invalid_peak,
    )
    assert decisions[MeasurementAnalysisFamily.SPATIAL].status is (
        MeasurementReadinessStatus.BLOCKED
    )
    assert decisions[MeasurementAnalysisFamily.SPATIAL].blocking_issues == (
        invalid_peak,
    )


def test_all_invalid_direct_peaks_block_direct_dependent_families_only():
    qualities = tuple(
        channel_quality(
            channel,
            (
                issue(
                    MeasurementQualityIssueCode.INVALID_DIRECT_PEAK,
                    channel=channel,
                ),
            ),
        )
        for channel in (ImpulseChannel.LEFT, ImpulseChannel.RIGHT)
    )

    decisions = by_family(
        MeasurementReadinessEngine().analyze(quality_analysis(qualities))
    )

    assert decisions[MeasurementAnalysisFamily.FREQUENCY].status is (
        MeasurementReadinessStatus.AVAILABLE
    )
    for family in (
        MeasurementAnalysisFamily.RT60,
        MeasurementAnalysisFamily.ETC,
        MeasurementAnalysisFamily.CLARITY,
        MeasurementAnalysisFamily.SPATIAL,
        MeasurementAnalysisFamily.DIRECT_REVERBERANT,
        MeasurementAnalysisFamily.BASS_DECAY,
    ):
        assert decisions[family].status is MeasurementReadinessStatus.BLOCKED


def test_spatial_requires_left_and_right_but_temporal_family_accepts_one_channel():
    missing_right = issue(
        MeasurementQualityIssueCode.MISSING_REQUIRED_CHANNEL,
        metric={"missing_channel": "RIGHT"},
    )
    quality = quality_analysis(
        (channel_quality(ImpulseChannel.LEFT),),
        (missing_right,),
    )

    decisions = by_family(MeasurementReadinessEngine().analyze(quality))

    spatial = decisions[MeasurementAnalysisFamily.SPATIAL]
    assert spatial.status is MeasurementReadinessStatus.BLOCKED
    assert spatial.required_channels == (
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
    )
    assert "CHANNEL_RIGHT" in spatial.missing_facts
    assert missing_right in spatial.blocking_issues
    assert decisions[MeasurementAnalysisFamily.RT60].status is (
        MeasurementReadinessStatus.AVAILABLE
    )


def test_global_timing_mismatch_blocks_spatial_but_is_reservation_for_etc():
    mismatch = issue(MeasurementQualityIssueCode.CHANNEL_TIMING_MISMATCH)
    quality = quality_analysis(
        (
            channel_quality(ImpulseChannel.LEFT),
            channel_quality(ImpulseChannel.RIGHT),
        ),
        (mismatch,),
    )

    decisions = by_family(MeasurementReadinessEngine().analyze(quality))

    assert mismatch in decisions[
        MeasurementAnalysisFamily.SPATIAL
    ].blocking_issues
    assert mismatch in decisions[
        MeasurementAnalysisFamily.ETC
    ].non_blocking_issues


def test_bass_decay_requires_a_channel_without_noise_or_dynamic_blocker():
    noisy = tuple(
        channel_quality(
            channel,
            (
                issue(
                    MeasurementQualityIssueCode.HIGH_NOISE_FLOOR,
                    channel=channel,
                ),
            ),
        )
        for channel in (ImpulseChannel.LEFT, ImpulseChannel.RIGHT)
    )

    decisions = by_family(
        MeasurementReadinessEngine().analyze(quality_analysis(noisy))
    )

    bass = decisions[MeasurementAnalysisFamily.BASS_DECAY]
    assert bass.status is MeasurementReadinessStatus.BLOCKED
    assert bass.missing_facts == ("ANY_ELIGIBLE_CHANNEL",)
    assert len(bass.blocking_issues) == 2
    assert decisions[MeasurementAnalysisFamily.ETC].status is (
        MeasurementReadinessStatus.AVAILABLE_WITH_RESERVATIONS
    )


def test_decisions_keep_applied_rules_and_technical_confidence():
    decision = by_family(
        MeasurementReadinessEngine().analyze(clean_quality())
    )[MeasurementAnalysisFamily.SPATIAL]

    assert decision.applied_rule_codes[0] == "REQUIRE_LEFT_RIGHT"
    assert "REQUIRE_VALID_SAMPLE_FACTS" in decision.applied_rule_codes
    assert "BLOCK_GLOBAL_CHANNEL_TIMING_MISMATCH" in (
        decision.applied_rule_codes
    )
    assert decision.confidence == 90.0


def test_status_cannot_contradict_structured_reasons():
    with pytest.raises(ValueError, match="status"):
        AnalysisReadiness(
            family=MeasurementAnalysisFamily.RT60,
            status=MeasurementReadinessStatus.AVAILABLE,
            missing_facts=("ANY_ELIGIBLE_CHANNEL",),
        )


class RecordingEngine:
    def __init__(self):
        self.input = None
        self.result = MeasurementReadinessAnalysis()

    def analyze(self, value):
        self.input = value
        return self.result


def test_stage_only_stores_the_structured_decision():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.measurement_quality_analysis = clean_quality()
    engine = RecordingEngine()

    MeasurementReadinessStage(engine).run(context)

    assert engine.input is context.measurement_quality_analysis
    assert context.measurement_readiness_analysis is engine.result


def test_pipeline_produces_readiness_but_does_not_branch_on_it():
    source = inspect.getsource(pipeline.BrainPipeline.run)
    readiness = source.index("MeasurementReadinessStage().run")
    analysis = source.index("AnalysisStage().run")

    assert readiness < analysis
    assert "measurement_readiness_analysis" not in source[readiness:analysis]
