import numpy as np
import pytest

from acousticbrain.analysis.etc import ETCAnalyzer
from acousticbrain.models import ImpulseChannel, ImpulseResponse


def impulse_with_reflections():
    sample_rate_hz = 48_000
    samples = np.random.default_rng(42).normal(0.0, 0.001, 4800)
    samples[482] = 1.0
    samples[490] = 0.8  # Trop proche du direct pour être un événement.
    samples[722] = 0.25
    samples[1202] = -0.1
    return ImpulseResponse(
        channel=ImpulseChannel.LEFT,
        sample_rate_hz=sample_rate_hz,
        samples=samples.tolist(),
        time_offset_seconds=-0.01,
        start_time_s=-0.01,
        peak_index=480,
        response_length=len(samples),
    )


def test_detects_direct_sound_and_factual_reflection_events():
    result = ETCAnalyzer().analyze(
        impulse_with_reflections(),
        analysis_window_ms=30.0,
    )

    assert result.channel is ImpulseChannel.LEFT
    assert result.direct_sound_index == 482
    assert result.direct_sound_time_s == pytest.approx(482 / 48_000 - 0.01)
    assert result.analysis_window_ms == 30.0
    assert result.noise_floor_db < -50.0
    assert len(result.events) == 2

    first, second = result.events
    assert first.sample_index == 722
    assert first.delay_ms == pytest.approx(5.0)
    assert first.relative_level_db == pytest.approx(-12.0412, abs=0.001)
    assert first.absolute_time_s == pytest.approx(722 / 48_000 - 0.01)
    assert first.acoustic_path_difference_m == pytest.approx(1.715)
    assert 0 < first.confidence <= 100

    assert second.sample_index == 1202
    assert second.delay_ms == pytest.approx(15.0)
    assert second.relative_level_db == pytest.approx(-20.0, abs=0.001)


def test_uses_global_maximum_when_rew_peak_is_not_locally_credible():
    impulse = impulse_with_reflections()
    impulse.peak_index = 3000

    result = ETCAnalyzer().analyze(impulse)

    assert result.direct_sound_index == 482


def test_returns_no_fact_when_direct_sound_is_undetectable():
    impulse = ImpulseResponse(
        channel=ImpulseChannel.RIGHT,
        sample_rate_hz=48_000,
        samples=[0.0] * 1000,
        peak_index=100,
    )

    result = ETCAnalyzer().analyze(impulse)

    assert result.direct_sound_index is None
    assert result.direct_sound_time_s is None
    assert result.events == []
    assert result.noise_floor_db is None
    assert result.confidence == 0.0


def test_rejects_invalid_impulse_or_analysis_window():
    analyzer = ETCAnalyzer()

    with pytest.raises(ValueError, match="sample rate"):
        analyzer.analyze(
            ImpulseResponse(
                channel=ImpulseChannel.STEREO,
                sample_rate_hz=0.0,
                samples=[1.0],
            )
        )

    with pytest.raises(ValueError, match="window"):
        analyzer.analyze(
            ImpulseResponse(
                channel=ImpulseChannel.STEREO,
                sample_rate_hz=48_000,
                samples=[1.0],
            ),
            analysis_window_ms=0.0,
        )
