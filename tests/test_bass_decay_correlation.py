import pytest

from acousticbrain.analysis import BassDecayCorrelationEngine
from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayBandAnalysis,
    BassDecayBandDifference,
    DecayUsability,
    DirectReverberantAnalysis,
    DirectReverberantBandAnalysis,
    EnergyWindowAnalysis,
    ModalBand,
    ModalDensityAnalysis,
    RoomMode,
    RoomModesAnalysis,
    RT60Analysis,
    RT60BandAnalysis,
)


def decay_band(center=63.0, value=1.2, confidence=90.0):
    return BassDecayBandAnalysis(
        center_frequency_hz=center,
        minimum_frequency_hz=56.0,
        maximum_frequency_hz=71.0,
        start_level_db=-5.0,
        end_level_db=-25.0,
        observed_decay_range_db=20.0,
        observed_duration_seconds=0.4,
        decay_slope_db_per_second=-60.0 / value,
        estimated_decay_time_seconds=value,
        noise_floor_db=-45.0,
        noise_margin_db=20.0,
        fit_correlation=-0.98,
        confidence=confidence,
        method="CHANNEL_MEAN",
        usability=DecayUsability.USABLE,
    )


def rt60_band(center=63.0, value=0.9, confidence=85.0):
    return RT60BandAnalysis(
        center_frequency_hz=center,
        minimum_frequency_hz=56.0,
        maximum_frequency_hz=71.0,
        rt60_seconds=value,
        decay_range_db=(-5.0, -35.0),
        fit_correlation=-0.99,
        confidence=confidence,
    )


def window(name, start, end):
    return EnergyWindowAnalysis(
        name=name,
        start_ms=start,
        end_ms=end,
        energy=1.0,
        relative_energy_db=-3.0,
        confidence=88.0,
        method="ENERGY",
    )


def drr_band(center=63.0, value=-3.0, confidence=88.0):
    return DirectReverberantBandAnalysis(
        center_frequency_hz=center,
        direct_window=window("DIRECT", 0.0, 5.0),
        early_window=window("EARLY", 5.0, 50.0),
        late_window=window("LATE", 50.0, 500.0),
        total_window=window("TOTAL", 0.0, 500.0),
        direct_to_reverberant_db=value,
        confidence=confidence,
        method="ENERGY",
    )


def base_analyses():
    bass_decay = BassDecayAnalysis(
        aggregate_bands=[decay_band()],
        left_right_band_differences=[
            BassDecayBandDifference(
                center_frequency_hz=63.0,
                difference_seconds=0.3,
                left_decay_time_seconds=1.2,
                right_decay_time_seconds=0.9,
                confidence=82.0,
                left_method="REGRESSION",
                right_method="REGRESSION",
            )
        ],
        confidence=88.0,
    )
    mode = RoomMode(axis="Longueur", order=1, frequency=63.5)
    room_modes = RoomModesAnalysis(
        modes=[mode],
        axial_modes=[mode],
        tangential_modes=[],
        oblique_modes=[],
        minimum_frequency_hz=20.0,
        maximum_frequency_hz=200.0,
        axial_count=1,
        tangential_count=0,
        oblique_count=0,
        total_count=1,
        confidence=86.0,
    )
    modal_density = ModalDensityAnalysis(
        bands=[ModalBand(50.0, 80.0, 1, 1 / 30, None, [63.5], [mode])],
        total_mode_count=1,
        confidence=84.0,
    )
    rt60 = RT60Analysis(
        aggregate_bands=[rt60_band()], confidence=85.0
    )
    drr = DirectReverberantAnalysis(
        aggregate_bands=[drr_band()], confidence=88.0
    )
    return bass_decay, room_modes, modal_density, rt60, drr


def test_produces_the_four_initial_structured_correlations():
    result = BassDecayCorrelationEngine().correlate(*base_analyses())

    assert [item.code for item in result.correlations] == [
        "SLOW_DECAY_MODAL_INTERACTION",
        "SLOW_DECAY_RT60_INTERACTION",
        "LOW_DRR_LONG_BASS_DECAY",
        "ASYMMETRIC_BASS_DECAY",
    ]
    assert result.confidence > 0.0
    assert result.source_analyses == (
        "BassDecayAnalysis",
        "RoomModesAnalysis",
        "ModalDensityAnalysis",
        "RT60Analysis",
        "DirectReverberantAnalysis",
    )


def test_modal_correlation_uses_band_bounds_and_modal_density_facts():
    correlation = BassDecayCorrelationEngine().correlate(
        *base_analyses()
    ).correlations[0]

    assert correlation.center_frequencies_hz == (63.0,)
    assert correlation.source_metrics == {
        "maximum_decay_time_s": 1.2,
        "matched_mode_count": 1,
        "maximum_local_mode_count": 1,
    }
    assert correlation.source_analyses == (
        "BassDecayAnalysis",
        "RoomModesAnalysis",
        "ModalDensityAnalysis",
    )
    assert correlation.confidence == 84.0
    assert 0.0 <= correlation.score <= 100.0
    match = correlation.modal_matches[0]
    assert match.band_center_frequency_hz == 63.0
    assert match.mode_frequency_hz == 63.5
    assert match.mode_type.value == "AXIAL"
    assert (match.order_x, match.order_y, match.order_z) == (1, 0, 0)
    assert match.frequency_error_hz == 0.5


def test_modal_correlation_requires_a_matching_density_band():
    bass, modes, density, rt60, drr = base_analyses()
    density.bands = []

    result = BassDecayCorrelationEngine().correlate(
        bass, modes, density, rt60, drr
    )

    assert all(
        item.code != "SLOW_DECAY_MODAL_INTERACTION"
        for item in result.correlations
    )


def test_rt60_and_drr_correlations_keep_source_metrics_and_confidence():
    result = BassDecayCorrelationEngine().correlate(*base_analyses())
    rt60 = next(
        item
        for item in result.correlations
        if item.code == "SLOW_DECAY_RT60_INTERACTION"
    )
    drr = next(
        item
        for item in result.correlations
        if item.code == "LOW_DRR_LONG_BASS_DECAY"
    )

    assert rt60.source_metrics["maximum_rt60_s"] == 0.9
    assert rt60.confidence == 85.0
    assert drr.source_metrics["minimum_drr_db"] == -3.0
    assert drr.confidence == 88.0


def test_asymmetry_uses_only_typed_left_right_differences():
    result = BassDecayCorrelationEngine().correlate(*base_analyses())
    correlation = next(
        item
        for item in result.correlations
        if item.code == "ASYMMETRIC_BASS_DECAY"
    )

    assert correlation.source_metrics == {
        "maximum_left_right_difference_s": 0.3,
        "asymmetric_band_count": 1.0,
    }
    assert correlation.confidence == 82.0
    assert correlation.source_analyses == ("BassDecayAnalysis",)


def test_produces_no_correlation_without_required_facts():
    empty_modes = RoomModesAnalysis([], [], [], [], 0.0, 0.0, 0, 0, 0, 0, 0.0)

    result = BassDecayCorrelationEngine().correlate(
        BassDecayAnalysis(),
        empty_modes,
        ModalDensityAnalysis(),
        RT60Analysis(),
        DirectReverberantAnalysis(),
    )

    assert result.correlations == []
    assert result.confidence == 0.0


def test_correlation_contract_rejects_unbounded_scores():
    from acousticbrain.models import BassDecayCorrelation

    with pytest.raises(ValueError, match="score"):
        BassDecayCorrelation(code="INVALID", score=101.0)
