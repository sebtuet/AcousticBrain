from dataclasses import asdict, fields

import pytest

from acousticbrain.models import (
    DirectReverberantAnalysis,
    DirectReverberantBandAnalysis,
    DirectReverberantChannelAnalysis,
    EnergyWindowAnalysis,
    ImpulseChannel,
)


def window(name, start, end, energy):
    return EnergyWindowAnalysis(
        name=name,
        start_ms=start,
        end_ms=end,
        energy=energy,
        relative_energy_db=0.0 if energy is not None else None,
        confidence=90.0,
        method="ENERGY_INTEGRATION",
    )


def band(ratio=3.0):
    return DirectReverberantBandAnalysis(
        center_frequency_hz=1000.0,
        direct_window=window("DIRECT", 0.0, 5.0, 4.0),
        early_window=window("EARLY", 5.0, 50.0, 1.0),
        late_window=window("LATE", 50.0, None, 1.0),
        total_window=window("TOTAL", 0.0, None, 6.0),
        direct_to_reverberant_db=ratio,
        confidence=90.0,
        method="THIRD_OCTAVE_ENERGY_WINDOWS",
    )


def test_energy_window_keeps_exact_bounds_and_method():
    result = window("DIRECT", -1.0, 5.0, 2.0)

    assert asdict(result) == {
        "name": "DIRECT",
        "start_ms": -1.0,
        "end_ms": 5.0,
        "energy": 2.0,
        "relative_energy_db": 0.0,
        "confidence": 90.0,
        "method": "ENERGY_INTEGRATION",
    }


def test_component_windows_cannot_overlap():
    with pytest.raises(ValueError, match="overlap"):
        DirectReverberantBandAnalysis(
            center_frequency_hz=1000.0,
            direct_window=window("DIRECT", 0.0, 10.0, 4.0),
            early_window=window("EARLY", 5.0, 50.0, 1.0),
            late_window=window("LATE", 50.0, None, 1.0),
            total_window=window("TOTAL", 0.0, None, 6.0),
            direct_to_reverberant_db=3.0,
            confidence=90.0,
            method="ENERGY_WINDOWS",
        )


@pytest.mark.parametrize(
    "direct, early, late",
    [(None, 1.0, 1.0), (4.0, None, 1.0), (4.0, 0.0, 0.0)],
)
def test_ratio_requires_exploitable_direct_and_reverberant_energy(
    direct, early, late
):
    with pytest.raises(ValueError, match="D/R requires"):
        DirectReverberantBandAnalysis(
            center_frequency_hz=1000.0,
            direct_window=window("DIRECT", 0.0, 5.0, direct),
            early_window=window("EARLY", 5.0, 50.0, early),
            late_window=window("LATE", 50.0, None, late),
            total_window=window("TOTAL", 0.0, None, None),
            direct_to_reverberant_db=3.0,
            confidence=0.0,
            method="ENERGY_WINDOWS",
        )


def test_unavailable_ratio_remains_explicitly_none():
    result = DirectReverberantBandAnalysis(
        center_frequency_hz=63.0,
        direct_window=window("DIRECT", 0.0, 5.0, None),
        early_window=window("EARLY", 5.0, 50.0, None),
        late_window=window("LATE", 50.0, None, None),
        total_window=window("TOTAL", 0.0, None, None),
        direct_to_reverberant_db=None,
        confidence=0.0,
        method="ENERGY_WINDOWS",
    )

    assert result.direct_to_reverberant_db is None


def test_channel_keeps_broadband_aggregates_and_configured_bounds():
    direct = window("DIRECT", 0.0, 5.0, 4.0)
    early = window("EARLY", 5.0, 50.0, 1.0)
    late = window("LATE", 50.0, 500.0, 1.0)
    total = window("TOTAL", 0.0, 500.0, 6.0)
    result = DirectReverberantChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        band_analyses=[band()],
        broadband_direct_window=direct,
        broadband_early_window=early,
        broadband_late_window=late,
        broadband_total_window=total,
        broadband_direct_to_reverberant_db=3.0,
        window_start_ms=0.0,
        direct_end_ms=5.0,
        early_end_ms=50.0,
        analysis_end_ms=500.0,
        confidence=90.0,
        method="BROADBAND_ENERGY_WINDOWS",
    )

    assert result.broadband_direct_window is direct
    assert result.analysis_end_ms == 500.0
    assert "samples" not in asdict(result)


def test_multi_channel_contract_keeps_typed_db_differences():
    left = DirectReverberantChannelAnalysis(channel=ImpulseChannel.LEFT)
    result = DirectReverberantAnalysis(
        channel_analyses={ImpulseChannel.LEFT: left},
        available_channels=(ImpulseChannel.LEFT,),
        aggregate_bands=[band()],
        common_center_frequencies_hz=(1000.0,),
        left_right_direct_to_reverberant_differences_db={1000.0: 1.5},
        confidence=90.0,
    )

    assert result.left_right_direct_to_reverberant_differences_db == {
        1000.0: 1.5
    }


def test_contract_contains_no_diagnostic_score_or_user_text():
    names = {
        item.name
        for model in (
            EnergyWindowAnalysis,
            DirectReverberantBandAnalysis,
            DirectReverberantChannelAnalysis,
            DirectReverberantAnalysis,
        )
        for item in fields(model)
    }
    assert names.isdisjoint(
        {"diagnostic", "message", "recommendation", "score", "severity"}
    )
