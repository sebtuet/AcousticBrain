import math

import numpy as np
import pytest

from acousticbrain.analysis import BassDecayAnalyzer
from acousticbrain.models import DecayUsability, ImpulseChannel, ImpulseResponse


def response(samples, sample_rate_hz=1000.0, peak_index=0):
    return ImpulseResponse(
        channel=ImpulseChannel.LEFT,
        sample_rate_hz=sample_rate_hz,
        samples=list(samples),
        peak_index=peak_index,
    )


def controlled_curve(monkeypatch, curve_db, noise_floor_db=-50.0):
    monkeypatch.setattr(
        BassDecayAnalyzer,
        "_filter",
        staticmethod(lambda samples, *_: np.asarray(samples, dtype=float)),
    )
    monkeypatch.setattr(
        BassDecayAnalyzer,
        "_energy_decay_curve",
        staticmethod(
            lambda _decay: (np.asarray(curve_db, dtype=float), noise_floor_db)
        ),
    )


def synthetic_bass_decay(
    decay_time_seconds=1.2,
    duration_seconds=3.0,
    sample_rate_hz=4000,
):
    count = round(duration_seconds * sample_rate_hz)
    time = np.arange(count) / sample_rate_hz
    envelope = np.exp(
        -math.log(1000.0) * time / decay_time_seconds
    )
    carrier = np.sin(2.0 * np.pi * 63.0 * time)
    samples = carrier * envelope
    samples[0] = 1.0
    return response(samples, sample_rate_hz=sample_rate_hz)


def test_estimates_a_usable_low_frequency_decay_from_one_impulse():
    result = BassDecayAnalyzer().analyze(
        synthetic_bass_decay(), center_frequencies_hz=(63.0,)
    )

    band = result.band_analyses[0]
    assert result.channel is ImpulseChannel.LEFT
    assert result.usable_band_count == 1
    assert band.usability is DecayUsability.USABLE
    assert band.estimated_decay_time_seconds == pytest.approx(1.2, rel=0.25)
    assert band.decay_slope_db_per_second < 0.0
    assert abs(band.fit_correlation) >= 0.90
    assert band.noise_floor_db is not None
    assert band.noise_margin_db >= 5.0
    assert 0.0 <= band.confidence <= 100.0


def test_assigns_insufficient_duration_before_attempting_a_regression():
    result = BassDecayAnalyzer().analyze(
        response([1.0] + [0.0] * 20),
        center_frequencies_hz=(63.0,),
    )

    band = result.band_analyses[0]
    assert band.usability is DecayUsability.INSUFFICIENT_DURATION
    assert band.estimated_decay_time_seconds is None


def test_assigns_insufficient_dynamic_range(monkeypatch):
    controlled_curve(monkeypatch, np.linspace(0.0, -12.0, 200))

    band = BassDecayAnalyzer().analyze(
        response(np.ones(200)), center_frequencies_hz=(63.0,)
    ).band_analyses[0]

    assert band.usability is DecayUsability.INSUFFICIENT_DYNAMIC_RANGE
    assert band.observed_decay_range_db == pytest.approx(12.0)
    assert band.estimated_decay_time_seconds is None


def test_assigns_noise_floor_reached_when_margin_is_insufficient(monkeypatch):
    controlled_curve(
        monkeypatch,
        np.linspace(0.0, -30.0, 200),
        noise_floor_db=-27.0,
    )

    band = BassDecayAnalyzer().analyze(
        response(np.ones(200)), center_frequencies_hz=(63.0,)
    ).band_analyses[0]

    assert band.usability is DecayUsability.NOISE_FLOOR_REACHED
    assert band.noise_margin_db == 2.0
    assert band.estimated_decay_time_seconds is None


def test_noise_floor_cause_precedes_apparent_dynamic_range_failure(monkeypatch):
    controlled_curve(
        monkeypatch,
        np.linspace(0.0, -12.0, 200),
        noise_floor_db=-27.0,
    )

    band = BassDecayAnalyzer().analyze(
        response(np.ones(200)), center_frequencies_hz=(63.0,)
    ).band_analyses[0]

    assert band.usability is DecayUsability.NOISE_FLOOR_REACHED


def test_assigns_unstable_slope_to_an_invalid_regression(monkeypatch):
    rng = np.random.default_rng(8)
    curve = np.concatenate(
        (np.array([0.0, -30.0]), rng.uniform(-24.0, -6.0, size=198))
    )
    controlled_curve(monkeypatch, curve)

    band = BassDecayAnalyzer().analyze(
        response(np.ones(200)), center_frequencies_hz=(63.0,)
    ).band_analyses[0]

    assert band.usability is DecayUsability.UNSTABLE_SLOPE
    assert band.fit_correlation is not None
    assert abs(band.fit_correlation) < 0.90
    assert band.estimated_decay_time_seconds is None


def test_aggregates_only_usable_band_confidences(monkeypatch):
    curve = np.linspace(0.0, -40.0, 400)
    controlled_curve(monkeypatch, curve)

    result = BassDecayAnalyzer().analyze(
        response(np.ones(400)), center_frequencies_hz=(50.0, 63.0)
    )

    assert result.usable_band_count == 2
    assert result.covered_frequency_range_hz == pytest.approx(
        (
            50.0 / BassDecayAnalyzer.BAND_EDGE_FACTOR,
            63.0 * BassDecayAnalyzer.BAND_EDGE_FACTOR,
        )
    )
    assert result.maximum_observed_duration_seconds is not None
    assert result.confidence > 0.0
    assert result.method == BassDecayAnalyzer.METHOD


@pytest.mark.parametrize(
    "impulse, message",
    [
        (response([], sample_rate_hz=1000.0), "samples"),
        (response([1.0], sample_rate_hz=0.0), "sample rate"),
        (response([1.0], peak_index=2), "peak index"),
    ],
)
def test_rejects_invalid_impulse_metadata(impulse, message):
    with pytest.raises(ValueError, match=message):
        BassDecayAnalyzer().analyze(impulse)


def test_uses_only_the_explicit_low_frequency_default_bands():
    result = BassDecayAnalyzer().analyze(
        synthetic_bass_decay(duration_seconds=0.02)
    )

    assert [band.center_frequency_hz for band in result.band_analyses] == list(
        BassDecayAnalyzer.THIRD_OCTAVE_CENTERS_HZ
    )
    assert min(band.center_frequency_hz for band in result.band_analyses) == 20.0
    assert max(band.center_frequency_hz for band in result.band_analyses) == 200.0
