from acousticbrain.analysis import ClarityCorrelationEngine
from acousticbrain.models import (
    ClarityAnalysis,
    ClarityBandAnalysis,
    ETCAnalysis,
    RT60Analysis,
    RT60BandAnalysis,
    ReflectionEvent,
)


def clarity_band(center=1000.0, c50=-3.0, d50=40.0, ts=0.1, confidence=90.0):
    return ClarityBandAnalysis(center, c50, 2.0, d50, ts, confidence, "ENERGY")


def rt60_band(center=1000.0, rt60=0.9, confidence=85.0):
    return RT60BandAnalysis(
        center_frequency_hz=center,
        minimum_frequency_hz=890.0,
        maximum_frequency_hz=1120.0,
        rt60_seconds=rt60,
        decay_range_db=(-5.0, -35.0),
        fit_correlation=0.99,
        confidence=confidence,
    )


def event(delay, level=-10.0, confidence=80.0):
    return ReflectionEvent(delay, level, delay / 1000.0, 1, 1.0, confidence)


def analyses():
    clarity = ClarityAnalysis(
        aggregate_bands=[clarity_band()],
        common_center_frequencies_hz=(1000.0,),
        confidence=88.0,
    )
    rt60 = RT60Analysis(
        aggregate_bands=[rt60_band()],
        common_center_frequencies_hz=(1000.0,),
        confidence=85.0,
    )
    etc = ETCAnalysis(
        common_events=[(event(delay), event(delay + 0.1)) for delay in range(5, 30, 5)],
        common_event_count=5,
        confidence=82.0,
    )
    return clarity, rt60, etc


def test_correlates_low_clarity_with_high_rt60_and_keeps_provenance():
    clarity, rt60, etc = analyses()

    result = ClarityCorrelationEngine().correlate(clarity, rt60, etc)

    correlation = next(item for item in result.correlations if item.code == "LOW_CLARITY_HIGH_RT60")
    assert correlation.center_frequencies_hz == (1000.0,)
    assert correlation.source_metrics["minimum_c50_db"] == -3.0
    assert correlation.source_metrics["maximum_rt60_s"] == 0.9
    assert correlation.source_analyses == ("ClarityAnalysis", "RT60Analysis")
    assert correlation.confidence == 85.0
    assert result.source_analyses == ("ClarityAnalysis", "RT60Analysis", "ETCAnalysis")


def test_correlates_low_clarity_with_dense_strong_early_events():
    clarity, rt60, etc = analyses()

    result = ClarityCorrelationEngine().correlate(clarity, rt60, etc)

    correlation = next(
        item
        for item in result.correlations
        if item.code == "LOW_CLARITY_DENSE_EARLY_REFLECTIONS"
    )
    assert correlation.source_metrics["strong_common_early_event_count"] == 5.0
    assert correlation.source_analyses == ("ClarityAnalysis", "ETCAnalysis")


def test_correlates_clarity_and_etc_asymmetries():
    clarity, rt60, etc = analyses()
    clarity.left_right_c50_differences_db = {1000.0: 3.0}
    etc.left_only_event_count = 7
    etc.right_only_event_count = 2

    result = ClarityCorrelationEngine().correlate(clarity, rt60, etc)

    correlation = next(
        item for item in result.correlations if item.code == "CLARITY_ETC_CHANNEL_ASYMMETRY"
    )
    assert correlation.center_frequencies_hz == (1000.0,)
    assert correlation.source_metrics["etc_specific_event_count_difference"] == 5.0


def test_correlates_high_center_time_with_late_decay():
    clarity, rt60, etc = analyses()

    result = ClarityCorrelationEngine().correlate(clarity, rt60, etc)

    correlation = next(item for item in result.correlations if item.code == "HIGH_CENTER_TIME_LATE_DECAY")
    assert correlation.source_metrics == {
        "maximum_ts_s": 0.1,
        "minimum_d50_percent": 40.0,
        "maximum_rt60_s": 0.9,
    }
    assert correlation.technical_basis_codes == (
        "TS_ABOVE_THRESHOLD",
        "D50_BELOW_THRESHOLD",
        "RT60_ABOVE_THRESHOLD",
    )


def test_does_not_invent_correlations_when_thresholds_are_not_met():
    clarity = ClarityAnalysis(
        aggregate_bands=[clarity_band(c50=4.0, d50=70.0, ts=0.04)],
        confidence=90.0,
    )
    rt60 = RT60Analysis(aggregate_bands=[rt60_band(rt60=0.4)], confidence=90.0)
    etc = ETCAnalysis(confidence=90.0)

    result = ClarityCorrelationEngine().correlate(clarity, rt60, etc)

    assert result.correlations == []
    assert result.confidence == 0.0
