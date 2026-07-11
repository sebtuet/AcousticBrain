import pytest

from acousticbrain.analysis import RT60Aggregator
from acousticbrain.models import (
    ImpulseChannel,
    RT60BandAnalysis,
    RT60ChannelAnalysis,
)


def band(center, rt60, confidence=90.0):
    return RT60BandAnalysis(
        center_frequency_hz=center,
        minimum_frequency_hz=center / 2**0.5,
        maximum_frequency_hz=center * 2**0.5,
        rt60_seconds=rt60,
        decay_range_db=(-5.0, -35.0),
        fit_correlation=0.99,
        confidence=confidence,
        t30_seconds=rt60,
        selected_estimate="T30",
        noise_floor_db=-60.0,
    )


def channel(channel, bands, broadband, confidence):
    return RT60ChannelAnalysis(
        channel=channel,
        band_analyses=bands,
        broadband_rt60_seconds=broadband,
        minimum_rt60_seconds=min(item.rt60_seconds for item in bands),
        maximum_rt60_seconds=max(item.rt60_seconds for item in bands),
        confidence=confidence,
    )


def test_aggregates_only_common_available_bands_and_channel_differences():
    left = channel(
        ImpulseChannel.LEFT,
        [band(500.0, 0.6), band(1000.0, 0.4)],
        broadband=0.5,
        confidence=90.0,
    )
    right = channel(
        ImpulseChannel.RIGHT,
        [band(1000.0, 0.5)],
        broadband=0.4,
        confidence=80.0,
    )

    result = RT60Aggregator().aggregate(
        {
            ImpulseChannel.RIGHT: right,
            ImpulseChannel.LEFT: left,
        }
    )

    assert result.available_channels == (
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
    )
    assert result.common_center_frequencies_hz == (1000.0,)
    assert len(result.aggregate_bands) == 1
    assert result.aggregate_bands[0].rt60_seconds == pytest.approx(0.45)
    assert result.aggregate_bands[0].selected_estimate == "CHANNEL_MEAN"
    assert result.left_right_band_differences_seconds == {
        1000.0: pytest.approx(-0.1)
    }
    assert result.interchannel_homogeneity == pytest.approx(77.7777778)
    assert result.broadband_rt60_seconds == pytest.approx(0.45)
    assert result.confidence == pytest.approx(42.5)


def test_returns_an_explicit_empty_analysis_without_channels():
    result = RT60Aggregator().aggregate({})

    assert result.channel_analyses == []
    assert result.available_channels == ()
    assert result.aggregate_bands == []
    assert result.broadband_rt60_seconds is None
    assert result.interchannel_homogeneity is None
    assert result.confidence == 0.0


def test_rejects_a_channel_key_that_does_not_match_the_analysis():
    left = channel(
        ImpulseChannel.LEFT,
        [band(1000.0, 0.4)],
        broadband=0.4,
        confidence=90.0,
    )

    with pytest.raises(ValueError, match="channel key"):
        RT60Aggregator().aggregate({ImpulseChannel.RIGHT: left})

