import pytest

from acousticbrain.analysis import DirectReverberantAggregator
from acousticbrain.models import (
    DirectReverberantBandAnalysis,
    DirectReverberantChannelAnalysis,
    EnergyWindowAnalysis,
    ImpulseChannel,
)


def window(name, start, end, energy, confidence=90.0):
    return EnergyWindowAnalysis(
        name=name,
        start_ms=start,
        end_ms=end,
        energy=energy,
        relative_energy_db=-3.0,
        confidence=confidence,
        method="ENERGY_WINDOWS",
    )


def band(center, ratio, confidence=90.0):
    return DirectReverberantBandAnalysis(
        center_frequency_hz=center,
        direct_window=window("DIRECT", 0.0, 5.0, 4.0, confidence),
        early_window=window("EARLY", 5.0, 50.0, 1.0, confidence),
        late_window=window("LATE", 50.0, 500.0, 1.0, confidence),
        total_window=window("TOTAL", 0.0, 500.0, 6.0, confidence),
        direct_to_reverberant_db=ratio,
        confidence=confidence,
        method="ENERGY_WINDOWS",
    )


def channel(channel_name, bands, broadband, confidence=90.0, direct_end=5.0):
    broadband_windows = (
        {
            "broadband_direct_window": window(
                "DIRECT", 0.0, direct_end, 4.0, confidence
            ),
            "broadband_early_window": window(
                "EARLY", direct_end, 50.0, 1.0, confidence
            ),
            "broadband_late_window": window(
                "LATE", 50.0, 500.0, 1.0, confidence
            ),
            "broadband_total_window": window(
                "TOTAL", 0.0, 500.0, 6.0, confidence
            ),
        }
        if broadband is not None
        else {}
    )
    return DirectReverberantChannelAnalysis(
        channel=channel_name,
        band_analyses=bands,
        broadband_direct_to_reverberant_db=broadband,
        window_start_ms=0.0,
        direct_end_ms=direct_end,
        early_end_ms=50.0,
        analysis_end_ms=500.0,
        confidence=confidence,
        method="BROADBAND_ENERGY_WINDOWS",
        **broadband_windows,
    )


def test_aggregates_common_bands_broadband_values_and_typed_differences():
    left = channel(
        ImpulseChannel.LEFT,
        [band(500.0, 1.0), band(1000.0, 3.0)],
        broadband=2.0,
        confidence=90.0,
    )
    right = channel(
        ImpulseChannel.RIGHT,
        [band(1000.0, 1.0, confidence=80.0)],
        broadband=1.0,
        confidence=80.0,
    )

    result = DirectReverberantAggregator().aggregate(
        {ImpulseChannel.RIGHT: right, ImpulseChannel.LEFT: left}
    )

    assert result.available_channels == (
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
    )
    assert result.common_center_frequencies_hz == (1000.0,)
    assert result.aggregate_bands[0].direct_to_reverberant_db == 2.0
    assert result.aggregate_bands[0].method == "CHANNEL_MEAN"
    assert result.left_right_direct_to_reverberant_differences_db == {
        1000.0: 2.0
    }
    assert result.broadband_direct_to_reverberant_db == 1.5
    assert result.minimum_broadband_direct_to_reverberant_db == 1.0
    assert result.maximum_broadband_direct_to_reverberant_db == 2.0
    assert result.confidence == pytest.approx(42.5)


def test_returns_an_explicit_empty_analysis():
    result = DirectReverberantAggregator().aggregate({})

    assert result.channel_analyses == {}
    assert result.available_channels == ()
    assert result.aggregate_bands == []
    assert result.broadband_direct_to_reverberant_db is None
    assert result.confidence == 0.0


def test_rejects_a_mismatched_channel_key():
    left = channel(ImpulseChannel.LEFT, [], broadband=None)

    with pytest.raises(ValueError, match="channel key"):
        DirectReverberantAggregator().aggregate({ImpulseChannel.RIGHT: left})


def test_rejects_incompatible_window_configurations():
    left = channel(ImpulseChannel.LEFT, [], broadband=None, direct_end=5.0)
    right = channel(ImpulseChannel.RIGHT, [], broadband=None, direct_end=6.0)

    with pytest.raises(ValueError, match="window configurations"):
        DirectReverberantAggregator().aggregate(
            {ImpulseChannel.LEFT: left, ImpulseChannel.RIGHT: right}
        )
