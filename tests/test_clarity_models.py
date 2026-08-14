from dataclasses import asdict, fields

from acousticbrain.models import (
    ClarityAnalysis,
    ClarityBandAnalysis,
    ClarityChannelAnalysis,
    ImpulseChannel,
)


def band(center_frequency_hz=1000.0):
    return ClarityBandAnalysis(
        center_frequency_hz=center_frequency_hz,
        c50_db=4.2,
        c80_db=7.5,
        d50_percent=72.5,
        ts_s=0.045,
        confidence=91.0,
        method="ENERGY_RATIOS",
    )


def test_band_analysis_keeps_only_temporal_energy_facts():
    analysis = band()

    assert asdict(analysis) == {
        "center_frequency_hz": 1000.0,
        "c50_db": 4.2,
        "c80_db": 7.5,
        "d50_percent": 72.5,
        "ts_s": 0.045,
        "confidence": 91.0,
        "method": "ENERGY_RATIOS",
    }


def test_band_analysis_represents_unavailable_metrics_explicitly():
    analysis = ClarityBandAnalysis(
        center_frequency_hz=63.0,
        c50_db=None,
        c80_db=None,
        d50_percent=None,
        ts_s=None,
        confidence=0.0,
        method=None,
    )

    assert analysis.c50_db is None
    assert analysis.c80_db is None
    assert analysis.d50_percent is None
    assert analysis.ts_s is None


def test_channel_analysis_aggregates_bands_without_raw_impulse_data():
    band_analysis = band()
    channel = ClarityChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        band_analyses=[band_analysis],
        broadband_c50_db=4.2,
        broadband_c80_db=7.5,
        broadband_d50_percent=72.5,
        broadband_ts_s=0.045,
        confidence=91.0,
    )

    assert channel.channel is ImpulseChannel.LEFT
    assert channel.band_analyses == [band_analysis]
    assert "samples" not in asdict(channel)


def test_multi_channel_analysis_keeps_common_bands_and_metric_differences():
    aggregate_band = band()
    left = ClarityChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        band_analyses=[band()],
        confidence=90.0,
    )
    right = ClarityChannelAnalysis(
        channel=ImpulseChannel.RIGHT,
        band_analyses=[band()],
        confidence=88.0,
    )
    analysis = ClarityAnalysis(
        channel_analyses={
            ImpulseChannel.LEFT: left,
            ImpulseChannel.RIGHT: right,
        },
        available_channels=(ImpulseChannel.LEFT, ImpulseChannel.RIGHT),
        aggregate_bands=[aggregate_band],
        common_center_frequencies_hz=(1000.0,),
        left_right_c50_differences_db={1000.0: 0.3},
        left_right_c80_differences_db={1000.0: 0.4},
        left_right_d50_differences_percent={1000.0: 2.5},
        left_right_ts_differences_s={1000.0: -0.004},
        confidence=89.0,
    )

    assert analysis.aggregate_bands == [aggregate_band]
    assert analysis.common_center_frequencies_hz == (1000.0,)
    assert analysis.left_right_c50_differences_db[1000.0] == 0.3
    assert analysis.left_right_ts_differences_s[1000.0] == -0.004


def test_clarity_contract_contains_no_score_or_user_text():
    field_names = {
        field.name
        for model in (
            ClarityBandAnalysis,
            ClarityChannelAnalysis,
            ClarityAnalysis,
        )
        for field in fields(model)
    }

    assert field_names.isdisjoint(
        {
            "diagnostic",
            "message",
            "recommendation",
            "recommendations",
            "score",
            "severity",
            "title",
        }
    )
