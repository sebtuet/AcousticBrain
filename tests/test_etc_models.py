from dataclasses import asdict, fields

from acousticbrain.models import (
    ETCAnalysis,
    ETCChannelAnalysis,
    ImpulseChannel,
    ReflectionEvent,
)


def event(delay_ms=5.0, confidence=92.0):
    return ReflectionEvent(
        delay_ms=delay_ms,
        relative_level_db=-12.5,
        absolute_time_s=0.105,
        sample_index=5040,
        acoustic_path_difference_m=1.715,
        confidence=confidence,
    )


def test_reflection_event_keeps_only_measured_temporal_facts():
    reflection = event()

    assert asdict(reflection) == {
        "delay_ms": 5.0,
        "relative_level_db": -12.5,
        "absolute_time_s": 0.105,
        "sample_index": 5040,
        "acoustic_path_difference_m": 1.715,
        "confidence": 92.0,
    }


def test_channel_analysis_separates_direct_sound_from_reflection_events():
    reflection = event()
    analysis = ETCChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        direct_sound_time_s=0.1,
        direct_sound_index=4800,
        events=[reflection],
        analysis_window_ms=50.0,
        noise_floor_db=-58.0,
        confidence=90.0,
    )

    assert analysis.channel is ImpulseChannel.LEFT
    assert analysis.direct_sound_index == 4800
    assert analysis.events == [reflection]
    assert analysis.noise_floor_db == -58.0


def test_channel_analysis_represents_an_unavailable_direct_sound_explicitly():
    analysis = ETCChannelAnalysis(
        channel=ImpulseChannel.SUB,
        direct_sound_time_s=None,
        direct_sound_index=None,
    )

    assert analysis.direct_sound_time_s is None
    assert analysis.direct_sound_index is None
    assert analysis.events == []
    assert analysis.confidence == 0.0


def test_etc_analysis_aggregates_channels_without_interpreting_events():
    left = ETCChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        direct_sound_time_s=0.1,
        direct_sound_index=4800,
        events=[event()],
        confidence=90.0,
    )
    right = ETCChannelAnalysis(
        channel=ImpulseChannel.RIGHT,
        direct_sound_time_s=0.1,
        direct_sound_index=4800,
        events=[event(delay_ms=5.2)],
        confidence=88.0,
    )
    analysis = ETCAnalysis(
        channels={
            ImpulseChannel.LEFT: left,
            ImpulseChannel.RIGHT: right,
        },
        available_channels=[ImpulseChannel.LEFT, ImpulseChannel.RIGHT],
        common_event_count=1,
        left_only_event_count=0,
        right_only_event_count=0,
        confidence=89.0,
    )

    assert analysis.channels[ImpulseChannel.LEFT] is left
    assert analysis.available_channels == [
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
    ]
    assert analysis.common_event_count == 1


def test_etc_contract_contains_no_interpretation_or_user_text():
    field_names = set()
    for model in (ReflectionEvent, ETCChannelAnalysis, ETCAnalysis):
        field_names.update(field.name for field in fields(model))

    assert field_names.isdisjoint(
        {
            "cause",
            "diagnostic",
            "message",
            "recommendation",
            "recommendations",
            "score",
            "severity",
            "surface",
            "title",
        }
    )
