from acousticbrain.analysis import DirectReverberantCorrelationEngine
from acousticbrain.models import (
    ClarityAnalysis,
    ClarityBandAnalysis,
    DirectReverberantAnalysis,
    DirectReverberantBandAnalysis,
    EnergyWindowAnalysis,
    ETCAnalysis,
    ETCChannelAnalysis,
    ImpulseChannel,
    ReflectionEvent,
    RT60Analysis,
    RT60BandAnalysis,
    SpatialAnalysis,
    SpatialChannelPairAnalysis,
    SpatialMeasurementType,
)


def window(name, start, end, energy):
    return EnergyWindowAnalysis(
        name, start, end, energy, -3.0, 90.0, "ENERGY_WINDOWS"
    )


def drr_band(center=1000.0, ratio=-3.0, confidence=90.0):
    return DirectReverberantBandAnalysis(
        center,
        window("DIRECT", 0.0, 5.0, 1.0),
        window("EARLY", 5.0, 50.0, 1.0),
        window("LATE", 50.0, 500.0, 1.0),
        window("TOTAL", 0.0, 500.0, 3.0),
        ratio,
        confidence,
        "ENERGY_WINDOWS",
    )


def rt60_band(center=1000.0, value=0.9, confidence=85.0):
    return RT60BandAnalysis(
        center,
        890.0,
        1120.0,
        value,
        (-5.0, -35.0),
        0.99,
        confidence,
    )


def base_analyses():
    drr = DirectReverberantAnalysis(
        aggregate_bands=[drr_band()],
        left_right_direct_to_reverberant_differences_db={1000.0: 4.0},
        confidence=88.0,
    )
    rt60 = RT60Analysis(aggregate_bands=[rt60_band()], confidence=85.0)
    events = [
        ReflectionEvent(10.0, -10.0, 0.01, index, 3.4, 82.0)
        for index in range(3)
    ]
    etc = ETCAnalysis(
        channels={
            ImpulseChannel.LEFT: ETCChannelAnalysis(
                ImpulseChannel.LEFT, 0.0, 0, events=events
            )
        },
        confidence=84.0,
    )
    clarity = ClarityAnalysis(
        aggregate_bands=[
            ClarityBandAnalysis(
                1000.0, 4.0, 6.0, 70.0, 0.04, 86.0, "ENERGY"
            )
        ],
        confidence=86.0,
    )
    pair = SpatialChannelPairAnalysis(
        measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        broadband_level_difference_db=2.0,
        confidence=80.0,
    )
    spatial = SpatialAnalysis(
        pair,
        SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        80.0,
    )
    return drr, rt60, etc, clarity, spatial


def test_correlates_low_drr_with_high_rt60():
    result = DirectReverberantCorrelationEngine().correlate(*base_analyses())

    correlation = next(
        item for item in result.correlations if item.code == "LOW_DRR_HIGH_RT60"
    )
    assert correlation.center_frequencies_hz == (1000.0,)
    assert correlation.source_metrics["minimum_drr_db"] == -3.0
    assert correlation.source_metrics["maximum_rt60_s"] == 0.9
    assert correlation.source_analyses == (
        "DirectReverberantAnalysis",
        "RT60Analysis",
    )
    assert correlation.confidence == 85.0


def test_correlates_low_drr_with_dominant_early_events():
    result = DirectReverberantCorrelationEngine().correlate(*base_analyses())

    correlation = next(
        item
        for item in result.correlations
        if item.code == "LOW_DRR_DOMINANT_EARLY_REFLECTIONS"
    )
    assert correlation.source_metrics["dominant_early_event_count"] == 3.0
    assert correlation.confidence == 82.0


def test_correlates_drr_and_spatial_channel_asymmetries():
    result = DirectReverberantCorrelationEngine().correlate(*base_analyses())

    correlation = next(
        item
        for item in result.correlations
        if item.code == "DRR_SPATIAL_CHANNEL_ASYMMETRY"
    )
    assert correlation.center_frequencies_hz == (1000.0,)
    assert correlation.source_metrics[
        "maximum_drr_channel_difference_db"
    ] == 4.0
    assert correlation.confidence == 80.0


def test_correlates_favorable_drr_with_high_clarity():
    drr, rt60, etc, clarity, spatial = base_analyses()
    drr.aggregate_bands = [drr_band(ratio=4.0)]

    result = DirectReverberantCorrelationEngine().correlate(
        drr, rt60, etc, clarity, spatial
    )

    correlation = next(
        item
        for item in result.correlations
        if item.code == "FAVORABLE_DRR_HIGH_CLARITY"
    )
    assert correlation.source_metrics == {
        "minimum_drr_db": 4.0,
        "minimum_c50_db": 4.0,
        "minimum_d50_percent": 70.0,
    }
    assert correlation.confidence == 86.0


def test_produces_no_correlation_without_required_facts():
    result = DirectReverberantCorrelationEngine().correlate(
        DirectReverberantAnalysis(),
        RT60Analysis(),
        ETCAnalysis(),
        ClarityAnalysis(),
        SpatialAnalysis(),
    )

    assert result.correlations == []
    assert result.confidence == 0.0
