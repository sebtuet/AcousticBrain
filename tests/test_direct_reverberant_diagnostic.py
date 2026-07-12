from acousticbrain.analysis import AnalysisContext
from acousticbrain.diagnostics import DirectReverberantDiagnostic
from acousticbrain.models import (
    DirectReverberantAnalysis,
    DirectReverberantChannelAnalysis,
    DirectReverberantCorrelation,
    DirectReverberantCorrelationAnalysis,
    ImpulseChannel,
    Measurement,
)


def test_reads_only_existing_drr_analysis_and_correlations():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    channel = DirectReverberantChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        broadband_direct_to_reverberant_db=None,
        confidence=88.0,
    )
    context.direct_reverberant_analysis = DirectReverberantAnalysis(
        channel_analyses={ImpulseChannel.LEFT: channel},
        available_channels=(ImpulseChannel.LEFT,),
        broadband_direct_to_reverberant_db=-2.0,
        left_right_direct_to_reverberant_differences_db={1000.0: 4.0},
        confidence=88.0,
    )
    context.direct_reverberant_correlation_analysis = (
        DirectReverberantCorrelationAnalysis(
            correlations=[
                DirectReverberantCorrelation(
                    code="LOW_DRR_HIGH_RT60",
                    score=75.0,
                    confidence=82.0,
                )
            ]
        )
    )

    diagnostic = DirectReverberantDiagnostic().analyze(context)

    assert diagnostic.severity == "HIGH"
    assert diagnostic.confidence == 88
    assert any("-2.00 dB" in item for item in diagnostic.observations)
    assert any("+4.00 dB" in item for item in diagnostic.observations)
    assert any("LOW_DRR_HIGH_RT60" in item for item in diagnostic.observations)


def test_handles_absent_analysis_explicitly():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    diagnostic = DirectReverberantDiagnostic().analyze(context)

    assert diagnostic.severity == "INFO"
    assert diagnostic.score is None


def test_keeps_favorable_correlation_as_observation_not_negative_cause():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.direct_reverberant_analysis = DirectReverberantAnalysis(
        broadband_direct_to_reverberant_db=1.38,
        confidence=90.0,
    )
    context.direct_reverberant_correlation_analysis = (
        DirectReverberantCorrelationAnalysis(
            correlations=[
                DirectReverberantCorrelation(
                    code="LOW_DRR_HIGH_RT60", score=80.0
                ),
                DirectReverberantCorrelation(
                    code="FAVORABLE_DRR_HIGH_CLARITY", score=100.0
                ),
            ]
        )
    )

    diagnostic = DirectReverberantDiagnostic().analyze(context)

    assert diagnostic.score == 41.5
    assert diagnostic.causes == ["LOW_DRR_HIGH_RT60"]
    assert any(
        "FAVORABLE_DRR_HIGH_CLARITY" in item
        for item in diagnostic.observations
    )
    assert "large bande est favorable" in diagnostic.conclusion
