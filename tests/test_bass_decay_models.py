from dataclasses import FrozenInstanceError

import pytest

from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayBandAnalysis,
    BassDecayBandDifference,
    BassDecayChannelAnalysis,
    DecayUsability,
    ImpulseChannel,
)


def usable_band(center=63.0):
    return BassDecayBandAnalysis(
        center_frequency_hz=center,
        minimum_frequency_hz=56.0,
        maximum_frequency_hz=71.0,
        start_level_db=-5.0,
        end_level_db=-30.0,
        observed_decay_range_db=25.0,
        observed_duration_seconds=0.8,
        decay_slope_db_per_second=-31.25,
        estimated_decay_time_seconds=1.92,
        noise_floor_db=-42.0,
        noise_margin_db=12.0,
        fit_correlation=-0.98,
        confidence=92.0,
        method="BAND_ENVELOPE_LINEAR_REGRESSION",
        usability=DecayUsability.USABLE,
    )


def test_models_expose_a_complete_usable_band_without_interpretation():
    band = usable_band()

    assert band.observed_decay_range_db == 25.0
    assert band.estimated_decay_time_seconds == 1.92
    assert band.noise_floor_db == -42.0
    assert band.noise_margin_db == 12.0
    assert band.usability is DecayUsability.USABLE
    with pytest.raises(FrozenInstanceError):
        band.confidence = 0.0


def test_unavailable_facts_remain_none_on_an_unusable_band():
    band = BassDecayBandAnalysis(
        center_frequency_hz=40.0,
        minimum_frequency_hz=35.0,
        maximum_frequency_hz=45.0,
        noise_floor_db=-35.0,
        confidence=20.0,
        method="BAND_ENVELOPE_LINEAR_REGRESSION",
        usability=DecayUsability.INSUFFICIENT_DYNAMIC_RANGE,
    )

    assert band.start_level_db is None
    assert band.decay_slope_db_per_second is None
    assert band.estimated_decay_time_seconds is None
    assert band.noise_margin_db is None


@pytest.mark.parametrize(
    "changes",
    [
        {"observed_decay_range_db": None},
        {"observed_duration_seconds": None},
        {"decay_slope_db_per_second": None},
        {"fit_correlation": None},
        {"noise_floor_db": None},
        {"noise_margin_db": None},
    ],
)
def test_usable_band_rejects_missing_required_physical_facts(changes):
    values = usable_band().__dict__ | changes

    with pytest.raises(ValueError):
        BassDecayBandAnalysis(**values)


def test_unusable_band_rejects_a_replacement_decay_time():
    with pytest.raises(ValueError):
        BassDecayBandAnalysis(
            center_frequency_hz=80.0,
            minimum_frequency_hz=71.0,
            maximum_frequency_hz=90.0,
            estimated_decay_time_seconds=0.0,
            usability=DecayUsability.UNSTABLE_SLOPE,
        )


def test_channel_count_must_match_structured_usability():
    band = usable_band()
    channel = BassDecayChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        band_analyses=[band],
        covered_frequency_range_hz=(56.0, 71.0),
        maximum_observed_duration_seconds=0.8,
        usable_band_count=1,
        confidence=92.0,
        method="BAND_ENVELOPE_LINEAR_REGRESSION",
    )

    assert channel.usable_band_count == 1
    with pytest.raises(ValueError):
        BassDecayChannelAnalysis(
            channel=ImpulseChannel.LEFT,
            band_analyses=[band],
            usable_band_count=0,
        )


def test_left_right_difference_is_signed_and_traceable():
    difference = BassDecayBandDifference(
        center_frequency_hz=63.0,
        difference_seconds=0.3,
        left_decay_time_seconds=1.2,
        right_decay_time_seconds=0.9,
        confidence=88.0,
        left_method="REGRESSION",
        right_method="REGRESSION",
    )

    assert difference.difference_seconds == pytest.approx(0.3)
    with pytest.raises(ValueError):
        BassDecayBandDifference(
            center_frequency_hz=63.0,
            difference_seconds=-0.3,
            left_decay_time_seconds=1.2,
            right_decay_time_seconds=0.9,
            confidence=88.0,
            left_method="REGRESSION",
            right_method="REGRESSION",
        )


def test_multichannel_contract_keeps_coverage_and_common_bands():
    band = usable_band()
    left = BassDecayChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        band_analyses=[band],
        covered_frequency_range_hz=(56.0, 71.0),
        maximum_observed_duration_seconds=0.8,
        usable_band_count=1,
        confidence=92.0,
        method="REGRESSION",
    )
    result = BassDecayAnalysis(
        channel_analyses={ImpulseChannel.LEFT: left},
        available_channels=(ImpulseChannel.LEFT,),
        aggregate_bands=[band],
        common_center_frequencies_hz=(63.0,),
        coverage=100.0,
        confidence=92.0,
    )

    assert result.channel_analyses[ImpulseChannel.LEFT] is left
    assert result.common_center_frequencies_hz == (63.0,)
    assert result.left_right_band_differences == []
