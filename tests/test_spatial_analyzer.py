import numpy as np
import pytest

from acousticbrain.analysis.spatial import SpatialAnalyzer
from acousticbrain.models import (
    ImpulseChannel,
    ImpulseResponse,
    SpatialChannelPairAnalysis,
    SpatialMeasurementType,
)


def response(channel, samples, peak_index, sample_rate_hz=1000.0):
    return ImpulseResponse(
        channel=channel,
        sample_rate_hz=sample_rate_hz,
        samples=list(samples),
        peak_index=peak_index,
    )


def identity_filter(monkeypatch):
    monkeypatch.setattr(
        SpatialAnalyzer,
        "_filter",
        staticmethod(lambda samples, *_: np.asarray(samples, dtype=float)),
    )


def test_calculates_neutral_pair_facts_without_interaural_aliases(monkeypatch):
    identity_filter(monkeypatch)
    first_samples = np.zeros(200)
    second_samples = np.zeros(200)
    first_samples[12:15] = [1.0, 0.5, 0.25]
    second_samples[10:13] = [0.5, 0.25, 0.125]

    result = SpatialAnalyzer().analyze(
        response(ImpulseChannel.LEFT, first_samples, 12),
        response(ImpulseChannel.RIGHT, second_samples, 10),
        SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        center_frequencies_hz=(100.0,),
        analysis_window_ms=100.0,
        maximum_correlation_delay_ms=10.0,
    )

    assert isinstance(result, SpatialChannelPairAnalysis)
    band = result.bands[0]
    assert band.level_difference_db == pytest.approx(6.0206)
    assert band.time_difference_ms == pytest.approx(2.0)
    assert band.cross_correlation == pytest.approx(1.0, abs=0.001)
    assert band.correlation_delay_ms == pytest.approx(2.0)
    assert band.interaural_level_difference_db is None
    assert band.interaural_time_difference_ms is None
    assert band.iacc is None


def test_populates_interaural_fields_only_for_a_binaural_protocol(monkeypatch):
    identity_filter(monkeypatch)
    first_samples = np.zeros(200)
    second_samples = np.zeros(200)
    first_samples[11] = 1.0
    second_samples[10] = 1.0

    band = SpatialAnalyzer().analyze(
        response(ImpulseChannel.LEFT, first_samples, 11),
        response(ImpulseChannel.RIGHT, second_samples, 10),
        SpatialMeasurementType.BINAURAL_PAIR,
        center_frequencies_hz=(100.0,),
    ).bands[0]

    assert band.interaural_level_difference_db == band.level_difference_db
    assert band.interaural_time_difference_ms == pytest.approx(1.0)
    assert band.iacc == pytest.approx(1.0, abs=0.001)


def test_filters_and_returns_requested_third_octave_bands():
    sample_rate_hz = 48000.0
    samples = np.zeros(12000)
    time = np.arange(6000) / sample_rate_hz
    samples[1000:7000] = np.sin(2 * np.pi * 1000.0 * time) * np.exp(-20.0 * time)

    result = SpatialAnalyzer().analyze(
        response(ImpulseChannel.LEFT, samples, 1000, sample_rate_hz),
        response(ImpulseChannel.RIGHT, samples * 0.8, 1000, sample_rate_hz),
        SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        center_frequencies_hz=(800.0, 1000.0, 1250.0),
    )

    assert [band.center_frequency_hz for band in result.bands] == [
        800.0,
        1000.0,
        1250.0,
    ]
    assert result.broadband_level_difference_db == pytest.approx(
        20.0 * np.log10(1.0 / 0.8), abs=0.01
    )
    assert result.broadband_cross_correlation == pytest.approx(1.0)
    assert result.confidence > 0.0


def test_keeps_unavailable_band_values_explicit(monkeypatch):
    identity_filter(monkeypatch)
    first = response(ImpulseChannel.LEFT, [1.0] + [0.0] * 99, 0)
    second = response(ImpulseChannel.RIGHT, [0.0] * 100, 0)

    result = SpatialAnalyzer().analyze(
        first,
        second,
        SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        center_frequencies_hz=(100.0,),
    )

    band = result.bands[0]
    assert band.level_difference_db is None
    assert band.cross_correlation is None
    assert band.confidence == 0.0


@pytest.mark.parametrize(
    "first, second, measurement_type, message",
    [
        (
            response(ImpulseChannel.LEFT, [1.0], 0, 48000.0),
            response(ImpulseChannel.RIGHT, [1.0], 0, 44100.0),
            SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
            "sample rates",
        ),
        (
            response(ImpulseChannel.LEFT, [1.0], 0),
            response(ImpulseChannel.LEFT, [1.0], 0),
            SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
            "distinct",
        ),
        (
            response(ImpulseChannel.LEFT, [1.0], 0),
            response(ImpulseChannel.RIGHT, [1.0], 0),
            None,
            "measurement type",
        ),
    ],
)
def test_rejects_incoherent_pair_inputs(first, second, measurement_type, message):
    with pytest.raises(ValueError, match=message):
        SpatialAnalyzer().analyze(first, second, measurement_type)
