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


def test_confidence_engine_includes_four_new_available_analyses():
    result = ConfidenceEngine().analyze(
        {
            "rt60": Analysis(confidence=94.0),
            "etc": Analysis(confidence=91.0),
            "clarity": Analysis(confidence=92.0),
            "spatial": Analysis(confidence=67.0),
        }
    )

    factors = {factor.source: factor for factor in result.factors}
    assert all(factors[source].available for source in ("rt60", "etc", "clarity", "spatial"))
    assert [factors[source].score for source in ("rt60", "etc", "clarity", "spatial")] == [
        94.0,
        91.0,
        92.0,
        67.0,
    ]
    assert result.available_evidence_count == 4
    assert result.missing_evidence_count == 0
    assert result.coverage_score == 100.0
    assert result.agreement_score == 73.0


def test_confidence_engine_keeps_partially_missing_new_evidence_unavailable():
    result = ConfidenceEngine().analyze(
        {
            "rt60": Analysis(confidence=90.0),
            "etc": None,
            "clarity": object(),
            "spatial": Analysis(confidence=70.0),
        }
    )

    factors = {factor.source: factor for factor in result.factors}
    assert factors["rt60"].available
    assert not factors["etc"].available
    assert not factors["clarity"].available
    assert factors["spatial"].available
    assert result.available_evidence_count == 2
    assert result.missing_evidence_count == 2
    assert result.coverage_score == 50.0
    assert result.agreement_score == 80.0


def test_confidence_engine_never_uses_an_acoustic_score_as_confidence():
    acoustic_analysis = type(
        "AcousticAnalysis",
        (),
        {"score": 5.0, "confidence": 88.0},
    )()

    result = ConfidenceEngine().analyze({"rt60": acoustic_analysis})

    assert result.factors[0].score == 88.0
    assert result.score != acoustic_analysis.score
