import numpy as np
import pytest

from acousticbrain.analysis.direct_reverberant import (
    DirectReverberantAnalyzer,
)
from acousticbrain.models import ImpulseChannel, ImpulseResponse


def response(samples, peak_index=10, sample_rate_hz=1000.0):
    return ImpulseResponse(
        channel=ImpulseChannel.LEFT,
        sample_rate_hz=sample_rate_hz,
        samples=list(samples),
        peak_index=peak_index,
    )


def identity_filter(monkeypatch):
    monkeypatch.setattr(
        DirectReverberantAnalyzer,
        "_filter",
        staticmethod(lambda samples, *_: np.asarray(samples, dtype=float)),
    )


def test_integrates_configured_windows_from_the_direct_sound(monkeypatch):
    identity_filter(monkeypatch)
    samples = np.zeros(100)
    samples[10:15] = 2.0
    samples[15:30] = 1.0
    samples[30:50] = 0.5

    result = DirectReverberantAnalyzer().analyze(
        response(samples),
        center_frequencies_hz=(100.0,),
        window_start_ms=0.0,
        direct_end_ms=5.0,
        early_end_ms=20.0,
        analysis_end_ms=40.0,
    )

    band = result.band_analyses[0]
    assert band.direct_window.energy == 20.0
    assert band.early_window.energy == 15.0
    assert band.late_window.energy == 5.0
    assert band.total_window.energy == 40.0
    assert band.direct_to_reverberant_db == pytest.approx(0.0)
    assert band.direct_window.start_ms == 0.0
    assert band.late_window.end_ms == 40.0
    assert result.window_start_ms == 0.0
    assert result.analysis_end_ms == 40.0


def test_uses_all_remaining_samples_when_analysis_end_is_none(monkeypatch):
    identity_filter(monkeypatch)
    samples = np.zeros(100)
    samples[10] = 2.0
    samples[20:] = 0.1

    band = DirectReverberantAnalyzer().analyze(
        response(samples),
        center_frequencies_hz=(100.0,),
        direct_end_ms=5.0,
        early_end_ms=10.0,
    ).band_analyses[0]

    assert band.late_window.end_ms is None
    assert band.total_window.end_ms is None
    assert band.late_window.energy > 0.0


def test_returns_none_when_reverberant_energy_is_insufficient(monkeypatch):
    identity_filter(monkeypatch)
    samples = np.zeros(100)
    samples[10] = 1.0

    band = DirectReverberantAnalyzer().analyze(
        response(samples),
        center_frequencies_hz=(100.0,),
    ).band_analyses[0]

    assert band.direct_to_reverberant_db is None
    assert band.direct_window.energy == 1.0
    assert band.early_window.energy == 0.0
    assert band.late_window.energy == 0.0


def test_keeps_all_energy_values_unavailable_for_an_empty_signal_band(monkeypatch):
    identity_filter(monkeypatch)

    band = DirectReverberantAnalyzer().analyze(
        response(np.zeros(100)),
        center_frequencies_hz=(100.0,),
    ).band_analyses[0]

    assert band.direct_window.energy is None
    assert band.early_window.energy is None
    assert band.late_window.energy is None
    assert band.total_window.energy is None
    assert band.direct_to_reverberant_db is None
    assert band.confidence == 0.0


def test_filters_requested_third_octave_bands_and_produces_broadband_facts():
    sample_rate_hz = 48000.0
    samples = np.zeros(24000)
    time = np.arange(12000) / sample_rate_hz
    samples[1000:13000] = np.cos(2 * np.pi * 1000.0 * time) * np.exp(
        -20.0 * time
    )

    result = DirectReverberantAnalyzer().analyze(
        response(samples, peak_index=1000, sample_rate_hz=sample_rate_hz),
        center_frequencies_hz=(800.0, 1000.0, 1250.0),
    )

    assert [band.center_frequency_hz for band in result.band_analyses] == [
        800.0,
        1000.0,
        1250.0,
    ]
    assert result.broadband_direct_window.energy is not None
    assert result.broadband_direct_to_reverberant_db is not None
    assert result.confidence > 0.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"window_start_ms": 5.0, "direct_end_ms": 5.0},
        {"direct_end_ms": 10.0, "early_end_ms": 5.0},
        {"early_end_ms": 50.0, "analysis_end_ms": 40.0},
    ],
)
def test_rejects_ambiguous_window_configuration(kwargs):
    with pytest.raises(ValueError, match="window|analysis end"):
        DirectReverberantAnalyzer().analyze(response([1.0] * 100), **kwargs)


def test_rejects_an_invalid_impulse_response():
    with pytest.raises(ValueError, match="samples"):
        DirectReverberantAnalyzer().analyze(
            ImpulseResponse(ImpulseChannel.LEFT, 48000.0, [])
        )
