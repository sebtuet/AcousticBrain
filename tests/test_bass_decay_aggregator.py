import pytest

from acousticbrain.analysis import BassDecayAggregator
from acousticbrain.models import (
    BassDecayBandAnalysis,
    BassDecayChannelAnalysis,
    DecayUsability,
    ImpulseChannel,
)


EDGE = 2 ** (1 / 6)


def band(center, decay_time, confidence=90.0, method="REGRESSION"):
    return BassDecayBandAnalysis(
        center_frequency_hz=center,
        minimum_frequency_hz=center / EDGE,
        maximum_frequency_hz=center * EDGE,
        start_level_db=-5.0,
        end_level_db=-25.0,
        observed_decay_range_db=20.0,
        observed_duration_seconds=0.4,
        decay_slope_db_per_second=-60.0 / decay_time,
        estimated_decay_time_seconds=decay_time,
        noise_floor_db=-45.0,
        noise_margin_db=20.0,
        fit_correlation=-0.98,
        confidence=confidence,
        method=method,
        usability=DecayUsability.USABLE,
    )


def unusable_band(center):
    return BassDecayBandAnalysis(
        center_frequency_hz=center,
        minimum_frequency_hz=center / EDGE,
        maximum_frequency_hz=center * EDGE,
        noise_floor_db=-20.0,
        confidence=0.0,
        method="REGRESSION",
        usability=DecayUsability.NOISE_FLOOR_REACHED,
    )


def channel(channel_name, bands, confidence=90.0, method="REGRESSION"):
    return BassDecayChannelAnalysis(
        channel=channel_name,
        band_analyses=bands,
        covered_frequency_range_hz=(
            bands[0].minimum_frequency_hz,
            bands[-1].maximum_frequency_hz,
        ) if bands else None,
        maximum_observed_duration_seconds=0.4 if bands else None,
        usable_band_count=sum(
            item.usability is DecayUsability.USABLE for item in bands
        ),
        confidence=confidence,
        method=method,
    )


def test_aggregates_common_usable_bands_and_typed_left_right_differences():
    left = channel(
        ImpulseChannel.LEFT,
        [band(50.0, 1.2), band(63.0, 1.0)],
        confidence=90.0,
    )
    right = channel(
        ImpulseChannel.RIGHT,
        [unusable_band(50.0), band(63.0, 0.8, confidence=80.0)],
        confidence=80.0,
    )

    result = BassDecayAggregator().aggregate(
        {ImpulseChannel.RIGHT: right, ImpulseChannel.LEFT: left}
    )

    assert result.available_channels == (
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
    )
    assert result.common_center_frequencies_hz == (63.0,)
    assert len(result.aggregate_bands) == 1
    aggregate = result.aggregate_bands[0]
    assert aggregate.estimated_decay_time_seconds == pytest.approx(0.9)
    assert aggregate.usability is DecayUsability.USABLE
    assert aggregate.method == "CHANNEL_MEAN"
    difference = result.left_right_band_differences[0]
    assert difference.center_frequency_hz == 63.0
    assert difference.difference_seconds == pytest.approx(0.2)
    assert difference.left_decay_time_seconds == 1.0
    assert difference.right_decay_time_seconds == 0.8
    assert difference.confidence == 80.0
    assert result.coverage == 50.0
    assert result.confidence == pytest.approx(42.5)


def test_single_channel_coverage_reflects_only_usable_analyzed_bands():
    left = channel(
        ImpulseChannel.LEFT,
        [band(50.0, 1.0), unusable_band(63.0)],
        confidence=80.0,
    )

    result = BassDecayAggregator().aggregate({ImpulseChannel.LEFT: left})

    assert result.common_center_frequencies_hz == (50.0,)
    assert result.coverage == 50.0
    assert result.confidence == 40.0
    assert result.left_right_band_differences == []


def test_returns_an_explicit_empty_analysis():
    result = BassDecayAggregator().aggregate({})

    assert result.channel_analyses == {}
    assert result.available_channels == ()
    assert result.aggregate_bands == []
    assert result.common_center_frequencies_hz == ()
    assert result.coverage == 0.0
    assert result.confidence == 0.0


def test_rejects_a_mismatched_channel_key():
    left = channel(ImpulseChannel.LEFT, [])

    with pytest.raises(ValueError, match="channel key"):
        BassDecayAggregator().aggregate({ImpulseChannel.RIGHT: left})


def test_rejects_duplicate_band_centers():
    left = channel(
        ImpulseChannel.LEFT,
        [band(63.0, 1.0), band(63.0, 1.1)],
    )

    with pytest.raises(ValueError, match="duplicate"):
        BassDecayAggregator().aggregate({ImpulseChannel.LEFT: left})


def test_rejects_incompatible_channel_methods():
    left = channel(ImpulseChannel.LEFT, [band(63.0, 1.0)], method="FIRST")
    right = channel(ImpulseChannel.RIGHT, [band(63.0, 1.0)], method="SECOND")

    with pytest.raises(ValueError, match="methods"):
        BassDecayAggregator().aggregate(
            {ImpulseChannel.LEFT: left, ImpulseChannel.RIGHT: right}
        )


def test_rejects_incompatible_band_bounds_for_the_same_center():
    left_band = band(63.0, 1.0)
    right_band = BassDecayBandAnalysis(
        **(
            left_band.__dict__
            | {
                "minimum_frequency_hz": 55.0,
                "maximum_frequency_hz": 72.0,
            }
        )
    )
    left = channel(ImpulseChannel.LEFT, [left_band])
    right = channel(ImpulseChannel.RIGHT, [right_band])

    with pytest.raises(ValueError, match="bounds"):
        BassDecayAggregator().aggregate(
            {ImpulseChannel.LEFT: left, ImpulseChannel.RIGHT: right}
        )
