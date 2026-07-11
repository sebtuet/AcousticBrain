from dataclasses import dataclass

from acousticbrain.analysis.confidence import ConfidenceEngine


@dataclass
class Analysis:
    confidence: float


def test_confidence_engine_aggregates_available_local_confidences():
    result = ConfidenceEngine().analyze(
        {
            "modal_density": Analysis(confidence=75),
            "sbir": Analysis(confidence=90),
            "stereo": None,
        }
    )

    assert result.available_evidence_count == 2
    assert result.missing_evidence_count == 1
    assert round(result.coverage_score, 1) == 66.7
    assert result.agreement_score == 85
    assert round(result.score, 1) == 79.2
    assert [factor.source for factor in result.factors] == [
        "modal_density",
        "sbir",
        "stereo",
        "coverage",
        "agreement",
    ]


def test_confidence_engine_reports_missing_evidence_without_creating_it():
    result = ConfidenceEngine().analyze(
        {
            "modal_density": None,
            "stereo": object(),
        }
    )

    assert result.score == 0
    assert result.available_evidence_count == 0
    assert result.missing_evidence_count == 2
    assert result.coverage_score == 0
    assert result.agreement_score == 0
    assert all(not factor.available for factor in result.factors[:2])
