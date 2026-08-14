from acousticbrain.analysis import SpatialCorrelationEngine
from acousticbrain.models import (
    ClarityAnalysis,
    ETCAnalysis,
    SpatialAlignmentStatus,
    SpatialAnalysis,
    SpatialBalanceStatus,
    SpatialCoherenceStatus,
    SpatialMeasurementType,
    SpatialStabilityStatus,
    SpeakerPairSpatialInterpretation,
    StereoAnalysis,
)


def interpretation(level, time, coherence, stability):
    return SpeakerPairSpatialInterpretation(
        measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        broadband_level_difference_db=2.5,
        broadband_time_difference_ms=0.4,
        broadband_cross_correlation=0.65,
        level_symmetry=level,
        relative_time_alignment=time,
        pair_coherence=coherence,
        technical_center_stability=stability,
        most_asymmetric_center_frequencies_hz=(1000.0,),
        confidence=90.0,
    )


def test_correlates_three_concordant_spatial_asymmetries():
    item = interpretation(
        SpatialBalanceStatus.ASYMMETRIC,
        SpatialAlignmentStatus.OFFSET,
        SpatialCoherenceStatus.WEAK,
        SpatialStabilityStatus.UNSTABLE,
    )
    stereo = StereoAnalysis(balance_low=3.0)
    etc = ETCAnalysis(left_only_event_count=7, right_only_event_count=2, confidence=85.0)
    clarity = ClarityAnalysis(
        left_right_c50_differences_db={1000.0: 3.0}, confidence=88.0
    )

    result = SpatialCorrelationEngine().correlate(
        SpatialAnalysis(), item, stereo, etc, clarity
    )

    assert [correlation.code for correlation in result.correlations] == [
        "SPATIAL_LEVEL_STEREO_IMBALANCE",
        "SPATIAL_TIME_ETC_CHANNEL_IMBALANCE",
        "SPATIAL_COHERENCE_CLARITY_ASYMMETRY",
    ]
    assert result.correlations[0].source_metrics["maximum_stereo_balance_db"] == 3.0
    assert result.correlations[2].center_frequencies_hz == (1000.0,)
    assert result.confidence > 0.0


def test_correlates_stable_center_only_when_all_analyses_agree():
    item = interpretation(
        SpatialBalanceStatus.BALANCED,
        SpatialAlignmentStatus.ALIGNED,
        SpatialCoherenceStatus.COHERENT,
        SpatialStabilityStatus.STABLE,
    )
    stereo = StereoAnalysis()
    etc = ETCAnalysis(confidence=90.0)
    clarity = ClarityAnalysis(confidence=90.0)

    result = SpatialCorrelationEngine().correlate(
        SpatialAnalysis(), item, stereo, etc, clarity
    )

    assert [correlation.code for correlation in result.correlations] == [
        "SPATIAL_TECHNICAL_CENTER_AGREEMENT"
    ]


def test_produces_no_partial_correlation_without_interpretation():
    result = SpatialCorrelationEngine().correlate(
        SpatialAnalysis(), None, StereoAnalysis(), ETCAnalysis(), ClarityAnalysis()
    )

    assert result.correlations == []
    assert result.confidence == 0.0
