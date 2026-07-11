import pytest

from acousticbrain.analysis import SpatialInterpretationEngine
from acousticbrain.models import (
    BinauralSpatialInterpretation,
    SpatialAlignmentStatus,
    SpatialAnalysis,
    SpatialBalanceStatus,
    SpatialBandAnalysis,
    SpatialChannelPairAnalysis,
    SpatialCoherenceStatus,
    SpatialMeasurementType,
    SpatialStabilityStatus,
    SpeakerPairSpatialInterpretation,
)


def band(center, level, time, correlation, measurement_type):
    binaural = measurement_type is SpatialMeasurementType.BINAURAL_PAIR
    return SpatialBandAnalysis(
        center_frequency_hz=center,
        level_difference_db=level,
        time_difference_ms=time,
        cross_correlation=correlation,
        correlation_delay_ms=time,
        interaural_level_difference_db=level if binaural else None,
        interaural_time_difference_ms=time if binaural else None,
        iacc=correlation if binaural else None,
        measurement_type=measurement_type,
        confidence=90.0,
        method="PAIR_CORRELATION",
    )


def spatial(pair):
    return SpatialAnalysis(
        pair_analysis=pair,
        source_measurement_type=pair.measurement_type,
        confidence=pair.confidence,
    )


def test_interprets_a_speaker_pair_as_technical_stability_only():
    measurement_type = SpatialMeasurementType.SPEAKER_CHANNEL_PAIR
    pair = SpatialChannelPairAnalysis(
        measurement_type=measurement_type,
        bands=[
            band(500.0, 0.5, 0.1, 0.95, measurement_type),
            band(1000.0, 3.0, 0.4, 0.6, measurement_type),
        ],
        broadband_level_difference_db=0.8,
        broadband_time_difference_ms=0.1,
        broadband_cross_correlation=0.94,
        confidence=91.0,
    )

    result = SpatialInterpretationEngine().interpret(spatial(pair))

    assert isinstance(result, SpeakerPairSpatialInterpretation)
    assert result.level_symmetry is SpatialBalanceStatus.BALANCED
    assert result.relative_time_alignment is SpatialAlignmentStatus.ALIGNED
    assert result.pair_coherence is SpatialCoherenceStatus.COHERENT
    assert result.technical_center_stability is SpatialStabilityStatus.STABLE
    assert result.most_asymmetric_center_frequencies_hz == (1000.0,)
    assert not hasattr(result, "iacc")


def test_marks_an_incoherent_speaker_pair_as_technically_unstable():
    pair = SpatialChannelPairAnalysis(
        measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        broadband_level_difference_db=2.0,
        broadband_time_difference_ms=0.3,
        broadband_cross_correlation=0.65,
    )

    result = SpatialInterpretationEngine().interpret(spatial(pair))

    assert result.level_symmetry is SpatialBalanceStatus.ASYMMETRIC
    assert result.relative_time_alignment is SpatialAlignmentStatus.OFFSET
    assert result.pair_coherence is SpatialCoherenceStatus.WEAK
    assert result.technical_center_stability is SpatialStabilityStatus.UNSTABLE


def test_exposes_only_existing_binaural_metrics():
    measurement_type = SpatialMeasurementType.BINAURAL_PAIR
    pair = SpatialChannelPairAnalysis(
        measurement_type=measurement_type,
        bands=[
            band(500.0, 1.0, 0.1, 0.92, measurement_type),
            band(1000.0, 2.0, 0.3, 0.75, measurement_type),
        ],
        confidence=88.0,
    )

    result = SpatialInterpretationEngine().interpret(spatial(pair))

    assert isinstance(result, BinauralSpatialInterpretation)
    assert result.interaural_level_differences_db == {
        500.0: 1.0,
        1000.0: 2.0,
    }
    assert result.interaural_time_differences_ms == {
        500.0: 0.1,
        1000.0: 0.3,
    }
    assert result.interaural_cross_correlations == {
        500.0: 0.92,
        1000.0: 0.75,
    }
    assert result.interaural_level_balance is SpatialBalanceStatus.ASYMMETRIC
    assert result.interaural_time_alignment is SpatialAlignmentStatus.OFFSET
    assert result.interaural_coherence is SpatialCoherenceStatus.PARTIAL


def test_returns_none_when_no_pair_analysis_exists():
    assert SpatialInterpretationEngine().interpret(SpatialAnalysis()) is None


def test_protocol_specific_model_rejects_the_wrong_measurement_type():
    with pytest.raises(ValueError, match="speaker channel pair"):
        SpeakerPairSpatialInterpretation(
            measurement_type=SpatialMeasurementType.BINAURAL_PAIR,
            broadband_level_difference_db=None,
            broadband_time_difference_ms=None,
            broadband_cross_correlation=None,
            level_symmetry=SpatialBalanceStatus.UNAVAILABLE,
            relative_time_alignment=SpatialAlignmentStatus.UNAVAILABLE,
            pair_coherence=SpatialCoherenceStatus.UNAVAILABLE,
            technical_center_stability=SpatialStabilityStatus.INDETERMINATE,
            most_asymmetric_center_frequencies_hz=(),
            confidence=0.0,
        )
