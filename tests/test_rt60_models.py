from dataclasses import asdict, fields

from acousticbrain.models import (
    ImpulseChannel,
    ImpulseResponse,
    RT60Analysis,
    RT60BandAnalysis,
    RT60ChannelAnalysis,
)


def band(center_frequency_hz=1000.0, rt60_seconds=0.42):
    return RT60BandAnalysis(
        center_frequency_hz=center_frequency_hz,
        minimum_frequency_hz=center_frequency_hz / 2**0.5,
        maximum_frequency_hz=center_frequency_hz * 2**0.5,
        rt60_seconds=rt60_seconds,
        decay_range_db=(-5.0, -35.0),
        fit_correlation=0.98,
        confidence=92.0,
    )


def test_impulse_response_keeps_only_raw_channel_samples():
    impulse = ImpulseResponse(
        channel=ImpulseChannel.LEFT,
        sample_rate_hz=48_000.0,
        samples=[0.0, 1.0, 0.25, -0.1],
        time_offset_seconds=-0.002,
        source_id="reference.left",
        peak_value=0.8,
        peak_index=1,
        response_length=4,
        sample_interval_s=1 / 48_000,
        start_time_s=-0.002,
    )

    assert impulse.channel is ImpulseChannel.LEFT
    assert impulse.sample_rate_hz == 48_000.0
    assert impulse.samples == [0.0, 1.0, 0.25, -0.1]
    assert impulse.response_length == 4
    assert "rt60_seconds" not in asdict(impulse)


def test_impulse_channel_codes_are_stable():
    assert [channel.value for channel in ImpulseChannel] == [
        "LEFT",
        "RIGHT",
        "STEREO",
        "SUB",
    ]


def test_rt60_band_analysis_keeps_decay_fit_facts():
    analysis = band()

    assert analysis.rt60_seconds == 0.42
    assert analysis.decay_range_db == (-5.0, -35.0)
    assert analysis.fit_correlation == 0.98
    assert analysis.confidence == 92.0
    assert analysis.edt_seconds is None
    assert analysis.selected_estimate is None


def test_rt60_channel_analysis_aggregates_one_channel():
    band_analysis = band()
    channel = RT60ChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        band_analyses=[band_analysis],
        broadband_rt60_seconds=0.42,
        minimum_rt60_seconds=0.42,
        maximum_rt60_seconds=0.42,
        confidence=92.0,
    )

    assert channel.channel is ImpulseChannel.LEFT
    assert channel.band_analyses == [band_analysis]
    assert channel.broadband_rt60_seconds == 0.42


def test_rt60_analysis_aggregates_multiple_channels_without_raw_samples():
    aggregate_band = band(rt60_seconds=0.45)
    left = RT60ChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        band_analyses=[band(rt60_seconds=0.42)],
        broadband_rt60_seconds=0.42,
        confidence=90.0,
    )
    right = RT60ChannelAnalysis(
        channel=ImpulseChannel.RIGHT,
        band_analyses=[band(rt60_seconds=0.48)],
        broadband_rt60_seconds=0.48,
        confidence=88.0,
    )
    analysis = RT60Analysis(
        channel_analyses=[left, right],
        aggregate_bands=[aggregate_band],
        broadband_rt60_seconds=0.45,
        minimum_rt60_seconds=0.42,
        maximum_rt60_seconds=0.48,
        confidence=89.0,
    )

    assert analysis.channel_analyses == [left, right]
    assert analysis.aggregate_bands == [aggregate_band]
    assert analysis.broadband_rt60_seconds == 0.45
    assert "samples" not in asdict(analysis)


def test_rt60_contract_contains_no_score_or_user_text():
    field_names = set()
    for model in (
        ImpulseResponse,
        RT60BandAnalysis,
        RT60ChannelAnalysis,
        RT60Analysis,
    ):
        field_names.update(field.name for field in fields(model))

    assert field_names.isdisjoint(
        {
            "diagnostic",
            "message",
            "recommendation",
            "recommendations",
            "score",
            "title",
        }
    )
