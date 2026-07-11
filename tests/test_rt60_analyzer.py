import math

import numpy as np
import pytest

from acousticbrain.analysis import RT60Analyzer
from acousticbrain.models import ImpulseChannel, ImpulseResponse


def synthetic_decay(rt60_seconds=0.6, duration_seconds=2.0, sample_rate_hz=24_000):
    sample_count = int(duration_seconds * sample_rate_hz)
    time_seconds = np.arange(sample_count) / sample_rate_hz
    envelope = np.exp(-math.log(1000.0) * time_seconds / rt60_seconds)
    samples = np.random.default_rng(42).normal(size=sample_count) * envelope
    return ImpulseResponse(
        channel=ImpulseChannel.LEFT,
        sample_rate_hz=sample_rate_hz,
        samples=samples.tolist(),
        peak_index=0,
        response_length=sample_count,
        sample_interval_s=1 / sample_rate_hz,
        start_time_s=0.0,
    )


def test_estimates_edt_t20_and_t30_in_third_octave_bands():
    result = RT60Analyzer().analyze(
        synthetic_decay(),
        center_frequencies_hz=(500.0, 1000.0, 2000.0),
    )

    assert result.channel is ImpulseChannel.LEFT
    assert len(result.band_analyses) == 3
    for band in result.band_analyses:
        assert band.edt_seconds == pytest.approx(0.6, rel=0.20)
        assert band.t20_seconds == pytest.approx(0.6, rel=0.15)
        assert band.t30_seconds == pytest.approx(0.6, rel=0.15)
        assert band.rt60_seconds == band.t30_seconds
        assert band.selected_estimate == "T30"
        assert band.fit_correlation > 0.98
        assert 0 < band.confidence <= 100

    assert result.broadband_rt60_seconds == pytest.approx(0.6, rel=0.15)
    assert result.minimum_rt60_seconds is not None
    assert result.maximum_rt60_seconds is not None


def test_falls_back_to_edt_when_later_decay_ranges_are_not_available():
    result = RT60Analyzer().analyze(
        synthetic_decay(rt60_seconds=0.8, duration_seconds=0.3),
        center_frequencies_hz=(1000.0,),
    )
    band = result.band_analyses[0]

    assert band.edt_seconds is not None
    assert band.t20_seconds is None
    assert band.t30_seconds is None
    assert band.selected_estimate == "EDT"
    assert band.rt60_seconds == band.edt_seconds
    assert band.confidence < 50.0


def test_keeps_unavailable_estimates_explicit_for_insufficient_decay():
    impulse = ImpulseResponse(
        channel=ImpulseChannel.RIGHT,
        sample_rate_hz=48_000,
        samples=[1.0] + [0.0] * 15,
        peak_index=0,
    )

    result = RT60Analyzer().analyze(
        impulse,
        center_frequencies_hz=(1000.0,),
    )
    band = result.band_analyses[0]

    assert band.edt_seconds is None
    assert band.t20_seconds is None
    assert band.t30_seconds is None
    assert band.rt60_seconds is None
    assert band.selected_estimate is None
    assert band.confidence == 0.0
    assert result.broadband_rt60_seconds is None
    assert result.confidence == 0.0


def test_rejects_invalid_raw_impulse_metadata():
    analyzer = RT60Analyzer()

    with pytest.raises(ValueError, match="sample rate"):
        analyzer.analyze(
            ImpulseResponse(
                channel=ImpulseChannel.STEREO,
                sample_rate_hz=0.0,
                samples=[1.0],
            )
        )

    with pytest.raises(ValueError, match="peak index"):
        analyzer.analyze(
            ImpulseResponse(
                channel=ImpulseChannel.STEREO,
                sample_rate_hz=48_000,
                samples=[1.0],
                peak_index=2,
            )
        )
