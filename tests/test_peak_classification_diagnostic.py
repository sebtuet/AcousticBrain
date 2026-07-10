from acousticbrain.analysis import AnalysisContext
from acousticbrain.diagnostics import PeakClassificationDiagnostic
from acousticbrain.models import (
    EvidenceLevel,
    Measurement,
    Peak,
    PeakClassification,
    PeakClassificationAnalysis,
    PeakClassificationType,
)


def classification(frequency, classification_type, confidence, evidence_level):
    return PeakClassification(
        peak=Peak(frequency, 80.0, 0, 8.0),
        classification=classification_type,
        confidence=confidence,
        evidence_level=evidence_level,
        explanation="Preuve physique existante",
    )


def test_peak_classification_diagnostic_interprets_existing_classifications():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.peak_classification = PeakClassificationAnalysis(
        classifications=[
            classification(
                63.5,
                PeakClassificationType.ROOM_MODE,
                96,
                EvidenceLevel.CONFIRMED,
            ),
            classification(
                75.0,
                PeakClassificationType.SBIR,
                72,
                EvidenceLevel.HYPOTHESIS,
            ),
            classification(
                367.0,
                PeakClassificationType.UNCLASSIFIED,
                0,
                EvidenceLevel.OBSERVED,
            ),
        ],
        score=67,
        confidence=84,
    )

    diagnostic = PeakClassificationDiagnostic().analyze(context)

    assert diagnostic.severity == "MEDIUM"
    assert diagnostic.score == 67
    assert diagnostic.confidence == 84
    assert diagnostic.evidence_level is EvidenceLevel.CONFIRMED
    assert "1 mode axial" in diagnostic.observations[0]
    assert "1 candidat SBIR" in diagnostic.observations[0]
    assert "2 pic(s) sur 3" in diagnostic.conclusion
    assert len(diagnostic.recommendations) == 3


def test_peak_classification_diagnostic_requires_an_analysis():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    diagnostic = PeakClassificationDiagnostic().analyze(context)

    assert diagnostic.severity == "INFO"
    assert diagnostic.confidence == 0
    assert "indisponible" in diagnostic.message
