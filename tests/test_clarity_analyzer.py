import math

import numpy as np
import pytest

from acousticbrain.analysis.clarity import ClarityAnalyzer
from acousticbrain.models import ImpulseChannel, ImpulseResponse


def decaying_impulse(*, sample_rate_hz=48000, duration_s=1.0, decay_rate=20.0):
    direct_index = 1000
    samples = np.zeros(round(sample_rate_hz * duration_s))
    time = np.arange(len(samples) - direct_index) / sample_rate_hz
    samples[direct_index:] = np.cos(2 * np.pi * 1000.0 * time) * np.exp(
        -decay_rate * time / 2
    )
    return ImpulseResponse(
        channel=ImpulseChannel.LEFT,
        sample_rate_hz=sample_rate_hz,
        samples=samples.tolist(),
        peak_index=direct_index,
    )


def test_calculates_energy_metrics_in_a_third_octave_band():
    analysis = ClarityAnalyzer().analyze(
        decaying_impulse(),
        center_frequencies_hz=(1000.0,),
    )

    band = analysis.band_analyses[0]
    expected_c50 = 10.0 * math.log10(math.exp(20.0 * 0.050) - 1.0)
    expected_c80 = 10.0 * math.log10(math.exp(20.0 * 0.080) - 1.0)

    assert band.c50_db == pytest.approx(expected_c50, abs=0.35)
    assert band.c80_db == pytest.approx(expected_c80, abs=0.35)
    assert band.d50_percent == pytest.approx(
        100.0 * (1.0 - math.exp(-20.0 * 0.050)),
        abs=1.0,
    )
    assert band.ts_s == pytest.approx(1.0 / 20.0, abs=0.003)
    assert band.method == ClarityAnalyzer.METHOD
    assert band.confidence > 0.0


def test_uses_direct_sound_as_the_time_origin():
    response = decaying_impulse()
    delayed = [0.0] * 500 + response.samples
    shifted = ImpulseResponse(
        channel=response.channel,
        sample_rate_hz=response.sample_rate_hz,
        samples=delayed,
        peak_index=response.peak_index + 500,
    )
    analyzer = ClarityAnalyzer()

    reference = analyzer.analyze(
        response,
        center_frequencies_hz=(1000.0,),
    ).band_analyses[0]
    result = analyzer.analyze(
        shifted,
        center_frequencies_hz=(1000.0,),
    ).band_analyses[0]

    assert result.c50_db == pytest.approx(reference.c50_db, abs=0.02)
    assert result.ts_s == pytest.approx(reference.ts_s, abs=0.0001)


def test_keeps_ratios_unavailable_when_late_energy_is_insufficient(monkeypatch):
    response = ImpulseResponse(
        channel=ImpulseChannel.RIGHT,
        sample_rate_hz=1000.0,
        samples=[1.0] + [0.0] * 199,
        peak_index=0,
    )
    monkeypatch.setattr(
        ClarityAnalyzer,
        "_filter",
        staticmethod(lambda samples, *_: np.asarray(samples, dtype=float)),
    )

    band = ClarityAnalyzer().analyze(
        response,
        center_frequencies_hz=(100.0,),
    ).band_analyses[0]

    assert band.c50_db is None
    assert band.c80_db is None
    assert band.d50_percent == 100.0
    assert band.ts_s == 0.0


def test_returns_only_channel_analysis_and_broadband_aggregates():
    result = ClarityAnalyzer().analyze(
        decaying_impulse(),
        center_frequencies_hz=(800.0, 1000.0, 1250.0),
    )

    assert result.channel is ImpulseChannel.LEFT
    assert len(result.band_analyses) == 3
    assert result.broadband_c50_db is not None
    assert result.broadband_c80_db is not None
    assert result.broadband_d50_percent is not None
    assert result.broadband_ts_s is not None


@pytest.mark.parametrize(
    "response",
    [
        ImpulseResponse(ImpulseChannel.LEFT, 0.0, [1.0]),
        ImpulseResponse(ImpulseChannel.LEFT, 48000.0, []),
        ImpulseResponse(ImpulseChannel.LEFT, 48000.0, [1.0], peak_index=2),
    ],
)
def test_rejects_invalid_impulse_responses(response):
    with pytest.raises(ValueError):
        ClarityAnalyzer().analyze(response)
