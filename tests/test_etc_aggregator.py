import pytest

from acousticbrain.analysis import ETCAggregator
from acousticbrain.models import (
    ETCChannelAnalysis,
    ImpulseChannel,
    ReflectionEvent,
)


def event(delay_ms, confidence=90.0):
    return ReflectionEvent(
        delay_ms=delay_ms,
        relative_level_db=-12.0,
        absolute_time_s=delay_ms / 1000.0,
        sample_index=round(delay_ms * 48),
        acoustic_path_difference_m=delay_ms / 1000.0 * 343.0,
        confidence=confidence,
    )


def channel(channel, events, confidence):
    return ETCChannelAnalysis(
        channel=channel,
        direct_sound_time_s=0.0,
        direct_sound_index=0,
        events=events,
        analysis_window_ms=50.0,
        noise_floor_db=-60.0,
        confidence=confidence,
    )


def test_matches_events_one_to_one_only_by_delay_proximity():
    left = channel(
        ImpulseChannel.LEFT,
        [event(5.0), event(10.0)],
        confidence=90.0,
    )
    right = channel(
        ImpulseChannel.RIGHT,
        [event(5.3), event(20.0)],
        confidence=80.0,
    )

    result = ETCAggregator().aggregate(
        {
            ImpulseChannel.RIGHT: right,
            ImpulseChannel.LEFT: left,
        },
        delay_tolerance_ms=0.5,
    )

    assert result.available_channels == [
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
    ]
    assert result.common_events == [(left.events[0], right.events[0])]
    assert result.left_only_events == [left.events[1]]
    assert result.right_only_events == [right.events[1]]
    assert result.common_event_count == 1
    assert result.left_only_event_count == 1
    assert result.right_only_event_count == 1
    assert result.confidence == pytest.approx(71.5)


def test_does_not_match_events_outside_the_explicit_tolerance():
    left = channel(ImpulseChannel.LEFT, [event(5.0)], confidence=90.0)
    right = channel(ImpulseChannel.RIGHT, [event(5.6)], confidence=90.0)

    result = ETCAggregator().aggregate(
        {
            ImpulseChannel.LEFT: left,
            ImpulseChannel.RIGHT: right,
        },
        delay_tolerance_ms=0.5,
    )

    assert result.common_events == []
    assert result.left_only_events == left.events
    assert result.right_only_events == right.events


def test_preserves_non_stereo_channels_without_inventing_matches():
    stereo = channel(
        ImpulseChannel.STEREO,
        [event(8.0)],
        confidence=88.0,
    )

    result = ETCAggregator().aggregate({ImpulseChannel.STEREO: stereo})

    assert result.channels == {ImpulseChannel.STEREO: stereo}
    assert result.available_channels == [ImpulseChannel.STEREO]
    assert result.common_event_count == 0
    assert result.confidence == 88.0


def test_rejects_invalid_tolerance_or_channel_mapping():
    left = channel(ImpulseChannel.LEFT, [], confidence=90.0)

    with pytest.raises(ValueError, match="tolerance"):
        ETCAggregator().aggregate(
            {ImpulseChannel.LEFT: left},
            delay_tolerance_ms=0.0,
        )

    with pytest.raises(ValueError, match="channel key"):
        ETCAggregator().aggregate({ImpulseChannel.RIGHT: left})

