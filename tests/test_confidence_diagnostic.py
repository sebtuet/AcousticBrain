from acousticbrain.analysis import AnalysisContext
from acousticbrain.diagnostics import ConfidenceDiagnostic
from acousticbrain.models import (
    ConfidenceAnalysis,
    ConfidenceFactor,
    Measurement,
)


def test_confidence_diagnostic_presents_existing_factors():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.confidence_analysis = ConfidenceAnalysis(
        score=72,
        factors=[
            ConfidenceFactor(
                source="modal_density",
                score=75,
                weight=1.0,
                available=True,
                explanation="Couverture limitée aux modes axiaux.",
            )
        ],
        available_evidence_count=2,
        missing_evidence_count=1,
        agreement_score=80,
        coverage_score=67,
    )

    diagnostic = ConfidenceDiagnostic().analyze(context)

    assert diagnostic.severity == "MEDIUM"
    assert diagnostic.score == 72
    assert diagnostic.confidence == 72
    assert "Couverture des preuves : 67 %" in diagnostic.observations[1]
    assert "modal_density : 75/100" in diagnostic.observations[3]
    assert len(diagnostic.recommendations) == 2


def test_confidence_diagnostic_requires_an_analysis():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    diagnostic = ConfidenceDiagnostic().analyze(context)

    assert diagnostic.severity == "INFO"
    assert diagnostic.confidence == 0
    assert "indisponible" in diagnostic.message
