from acousticbrain.analysis import AnalysisContext
from acousticbrain.diagnostics import ClarityDiagnostic
from acousticbrain.models import (
    ClarityAnalysis,
    ClarityChannelAnalysis,
    ClarityCorrelation,
    ClarityCorrelationAnalysis,
    ImpulseChannel,
    Measurement,
)


def context_with_clarity():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    left = ClarityChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        broadband_c50_db=-2.0,
        broadband_c80_db=1.5,
        broadband_d50_percent=38.0,
        broadband_ts_s=0.095,
        confidence=88.0,
    )
    context.clarity_analysis = ClarityAnalysis(
        channel_analyses={ImpulseChannel.LEFT: left},
        available_channels=(ImpulseChannel.LEFT,),
        common_center_frequencies_hz=(1000.0,),
        left_right_c50_differences_db={1000.0: 3.0},
        confidence=88.0,
    )
    return context


def test_presents_existing_metrics_and_correlations_without_recalculation():
    context = context_with_clarity()
    correlation = ClarityCorrelation(
        code="LOW_CLARITY_HIGH_RT60",
        center_frequencies_hz=(1000.0,),
        source_metrics={"minimum_c50_db": -3.0, "maximum_rt60_s": 0.9},
        source_analyses=("ClarityAnalysis", "RT60Analysis"),
        score=75.0,
        confidence=82.0,
        technical_basis_codes=("C50_BELOW_THRESHOLD", "RT60_ABOVE_THRESHOLD"),
    )
    context.clarity_correlation_analysis = ClarityCorrelationAnalysis(
        correlations=[correlation],
        confidence=82.0,
    )

    diagnostic = ClarityDiagnostic().analyze(context)

    assert diagnostic.severity == "MEDIUM"
    assert diagnostic.score == 80.0
    assert diagnostic.confidence == 82
    assert any("C50 -2.0 dB" in item for item in diagnostic.observations)
    assert any("C80 1.5 dB" in item for item in diagnostic.observations)
    assert any("D50 38.0 %" in item for item in diagnostic.observations)
    assert any("Ts 0.095 s" in item for item in diagnostic.observations)
    assert any("LOW_CLARITY_HIGH_RT60" in item for item in diagnostic.observations)


def test_handles_absent_analysis_explicitly():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    diagnostic = ClarityDiagnostic().analyze(context)

    assert diagnostic.severity == "INFO"
    assert diagnostic.score is None
    assert diagnostic.confidence == 0


def test_does_not_create_a_problem_without_structured_correlations():
    context = context_with_clarity()
    context.clarity_correlation_analysis = ClarityCorrelationAnalysis()

    diagnostic = ClarityDiagnostic().analyze(context)

    assert diagnostic.severity == "LOW"
    assert diagnostic.score == 100.0
    assert "Aucune corrélation" in diagnostic.conclusion
