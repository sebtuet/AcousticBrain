from dataclasses import asdict, fields

import pytest

from acousticbrain.models import (
    SpatialAnalysis,
    SpatialBandAnalysis,
    SpatialChannelPairAnalysis,
    SpatialMeasurementType,
)


def speaker_band():
    return SpatialBandAnalysis(
        center_frequency_hz=1000.0,
        level_difference_db=1.2,
        time_difference_ms=-0.15,
        cross_correlation=0.94,
        correlation_delay_ms=-0.125,
        interaural_level_difference_db=None,
        interaural_time_difference_ms=None,
        iacc=None,
        measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        confidence=92.0,
        method="THIRD_OCTAVE_CROSS_CORRELATION",
    )


def test_speaker_pair_band_keeps_neutral_pair_facts():
    band = speaker_band()

    assert asdict(band) == {
        "center_frequency_hz": 1000.0,
        "level_difference_db": 1.2,
        "time_difference_ms": -0.15,
        "cross_correlation": 0.94,
        "correlation_delay_ms": -0.125,
        "interaural_level_difference_db": None,
        "interaural_time_difference_ms": None,
        "iacc": None,
        "measurement_type": SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        "confidence": 92.0,
        "method": "THIRD_OCTAVE_CROSS_CORRELATION",
    }


@pytest.mark.parametrize(
    "metric, value",
    [
        ("interaural_level_difference_db", 1.2),
        ("interaural_time_difference_ms", -0.15),
        ("iacc", 0.94),
    ],
)
def test_speaker_pair_rejects_interaural_metrics(metric, value):
    values = asdict(speaker_band())
    values[metric] = value

    with pytest.raises(ValueError, match="binaural"):
        SpatialBandAnalysis(**values)


def test_binaural_pair_can_carry_interaural_facts():
    band = SpatialBandAnalysis(
        center_frequency_hz=1000.0,
        level_difference_db=1.2,
        time_difference_ms=-0.15,
        cross_correlation=0.94,
        correlation_delay_ms=-0.125,
        interaural_level_difference_db=1.2,
        interaural_time_difference_ms=-0.15,
        iacc=0.94,
        measurement_type=SpatialMeasurementType.BINAURAL_PAIR,
        confidence=92.0,
        method="BINAURAL_CROSS_CORRELATION",
    )

    assert band.iacc == 0.94
    assert band.measurement_type is SpatialMeasurementType.BINAURAL_PAIR


def test_pair_analysis_requires_one_measurement_protocol():
    with pytest.raises(ValueError, match="measurement type"):
        SpatialChannelPairAnalysis(
            measurement_type=SpatialMeasurementType.BINAURAL_PAIR,
            bands=[speaker_band()],
        )


def test_spatial_analysis_keeps_absence_explicit():
    analysis = SpatialAnalysis()

    assert analysis.pair_analysis is None
    assert analysis.source_measurement_type is None
    assert analysis.confidence == 0.0


def test_spatial_analysis_preserves_pair_provenance():
    pair = SpatialChannelPairAnalysis(
        measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        bands=[speaker_band()],
        broadband_level_difference_db=1.0,
        broadband_time_difference_ms=-0.1,
        broadband_cross_correlation=0.95,
        confidence=92.0,
        method="CROSS_CORRELATION",
    )
    analysis = SpatialAnalysis(
        pair_analysis=pair,
        source_measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        confidence=92.0,
    )

    assert analysis.pair_analysis is pair
    assert analysis.source_measurement_type is pair.measurement_type


def test_spatial_contract_contains_no_perceptual_conclusion_or_score():
    field_names = {
        field.name
        for model in (
            SpatialBandAnalysis,
            SpatialChannelPairAnalysis,
            SpatialAnalysis,
        )
        for field in fields(model)
    }

    assert field_names.isdisjoint(
        {
            "diagnostic",
            "localization",
            "phantom_center_stability",
            "recommendation",
            "score",
            "severity",
            "stage_width",
        }
    )
