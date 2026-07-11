from acousticbrain.models import ConfidenceAnalysis, ConfidenceFactor


def test_confidence_analysis_keeps_its_evidence_factors():
    factor = ConfidenceFactor(
        source="ModalDensityAnalysis",
        score=75.0,
        weight=0.4,
        available=True,
        explanation="Couverture limitée aux modes axiaux.",
    )

    analysis = ConfidenceAnalysis(
        score=82.0,
        factors=[factor],
        available_evidence_count=3,
        missing_evidence_count=1,
        agreement_score=90.0,
        coverage_score=75.0,
    )

    assert analysis.factors == [factor]
    assert analysis.available_evidence_count == 3
    assert analysis.missing_evidence_count == 1
    assert analysis.agreement_score == 90.0
    assert analysis.coverage_score == 75.0
