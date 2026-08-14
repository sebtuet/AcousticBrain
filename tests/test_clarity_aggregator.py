import pytest

from acousticbrain.analysis import ClarityAggregator
from acousticbrain.models import (
    ClarityBandAnalysis,
    ClarityChannelAnalysis,
    ImpulseChannel,
)


def band(center, c50, c80, d50, ts, confidence=90.0):
    return ClarityBandAnalysis(
        center_frequency_hz=center,
        c50_db=c50,
        c80_db=c80,
        d50_percent=d50,
        ts_s=ts,
        confidence=confidence,
        method="THIRD_OCTAVE_ENERGY_INTEGRATION",
    )


def channel(channel_name, bands, confidence=90.0):
    return ClarityChannelAnalysis(
        channel=channel_name,
        band_analyses=bands,
        confidence=confidence,
    )


def test_aggregates_common_bands_and_keeps_each_difference_typed():
    left = channel(
        ImpulseChannel.LEFT,
        [band(500.0, 3.0, 5.0, 60.0, 0.060), band(1000.0, 4.0, 7.0, 70.0, 0.050)],
    )
    right = channel(
        ImpulseChannel.RIGHT,
        [band(1000.0, 3.0, 5.0, 65.0, 0.060, confidence=80.0)],
        confidence=80.0,
    )

    result = ClarityAggregator().aggregate(
        {ImpulseChannel.RIGHT: right, ImpulseChannel.LEFT: left}
    )

    assert result.available_channels == (ImpulseChannel.LEFT, ImpulseChannel.RIGHT)
    assert result.common_center_frequencies_hz == (1000.0,)
    aggregate = result.aggregate_bands[0]
    assert aggregate.c50_db == pytest.approx(3.5)
    assert aggregate.c80_db == pytest.approx(6.0)
    assert aggregate.d50_percent == pytest.approx(67.5)
    assert aggregate.ts_s == pytest.approx(0.055)
    assert aggregate.method == "CHANNEL_MEAN"
    assert result.left_right_c50_differences_db == {1000.0: 1.0}
    assert result.left_right_c80_differences_db == {1000.0: 2.0}
    assert result.left_right_d50_differences_percent == {1000.0: 5.0}
    assert result.left_right_ts_differences_s[1000.0] == pytest.approx(-0.010)
    assert 0.0 < result.confidence < 85.0


def test_omits_only_the_unavailable_metric_difference():
    left = channel(ImpulseChannel.LEFT, [band(1000.0, None, 5.0, 60.0, 0.06)])
    right = channel(ImpulseChannel.RIGHT, [band(1000.0, 3.0, 4.0, 55.0, 0.07)])

    result = ClarityAggregator().aggregate(
        {ImpulseChannel.LEFT: left, ImpulseChannel.RIGHT: right}
    )

    assert result.left_right_c50_differences_db == {}
    assert result.left_right_c80_differences_db == {1000.0: 1.0}


def test_returns_an_explicit_empty_analysis():
    result = ClarityAggregator().aggregate({})

    assert result.channel_analyses == {}
    assert result.available_channels == ()
    assert result.aggregate_bands == []
    assert result.confidence == 0.0


def test_rejects_a_mismatched_channel_key():
    left = channel(ImpulseChannel.LEFT, [])

    with pytest.raises(ValueError, match="channel key"):
        ClarityAggregator().aggregate({ImpulseChannel.RIGHT: left})
