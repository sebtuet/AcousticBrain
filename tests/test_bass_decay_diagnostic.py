from acousticbrain.analysis import AnalysisContext
import pytest
from acousticbrain.diagnostics import BassDecayDiagnostic
from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayBandAnalysis,
    BassDecayCorrelation,
    BassDecayCorrelationAnalysis,
    DecayUsability,
    Measurement,
)


def band():
    return BassDecayBandAnalysis(
        63.0, 56.0, 71.0, -5.0, -25.0, 20.0, 0.4,
        -50.0, 1.2, -45.0, 20.0, -0.98, 84.0,
        "CHANNEL_MEAN", DecayUsability.USABLE,
    )


def test_diagnostic_reads_only_structured_bass_decay_knowledge():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.bass_decay_analysis = BassDecayAnalysis(
        aggregate_bands=[band()], coverage=50.0, confidence=84.0
    )
    context.bass_decay_correlation_analysis = BassDecayCorrelationAnalysis(
        correlations=[
            BassDecayCorrelation(
                code="SLOW_DECAY_MODAL_INTERACTION",
                score=75.0,
                confidence=80.0,
            )
        ]
    )

    diagnostic = BassDecayDiagnostic().analyze(context)

    assert diagnostic.title == "Décroissance dans le grave"
    assert diagnostic.severity == "MEDIUM"
    assert diagnostic.score == pytest.approx(61.6666667)
    assert diagnostic.confidence == 84
    assert diagnostic.causes == ["SLOW_DECAY_MODAL_INTERACTION"]
    assert any("1.200 s" in item for item in diagnostic.observations)
    assert any("excitation modale" in item for item in diagnostic.recommendations)


def test_diagnostic_reports_unavailable_common_bands_explicitly():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.bass_decay_analysis = BassDecayAnalysis()

    diagnostic = BassDecayDiagnostic().analyze(context)

    assert diagnostic.severity == "INFO"
    assert diagnostic.score is None
