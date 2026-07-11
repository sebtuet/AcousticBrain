from dataclasses import dataclass, field

from acousticbrain.analysis import GlobalSynthesizer
from acousticbrain.models import ModalDensityAnalysis


@dataclass
class Classification:
    classification: str


@dataclass
class PeakClassificationAnalysis:
    score: float
    confidence: float
    classifications: list[Classification] = field(default_factory=list)


@dataclass
class ConfidenceAnalysis:
    score: float


@dataclass
class StereoAnalysis:
    symmetry_score: float


@dataclass
class SBIRAnalysis:
    score: float
    confidence: float


def test_aggregates_available_scores_and_orders_priority_domains():
    modal = ModalDensityAnalysis(score=70.0, confidence=80.0)
    peaks = PeakClassificationAnalysis(score=40.0, confidence=60.0)

    result = GlobalSynthesizer().synthesize(
        modal_density=modal,
        peak_classification=peaks,
        confidence=ConfidenceAnalysis(score=75.0),
    )

    assert result.score == 55.0
    assert result.confidence == 75.0
    assert result.priority_domains == ("PEAK_CLASSIFICATION", "MODAL_DENSITY")
    assert result.source_analyses == (
        "ModalDensityAnalysis",
        "PeakClassificationAnalysis",
    )


def test_derives_recommendation_codes_from_physical_findings():
    modal = ModalDensityAnalysis(score=70.0, confidence=80.0)
    peaks = PeakClassificationAnalysis(
        score=60.0,
        confidence=70.0,
        classifications=[Classification("UNCLASSIFIED")],
    )

    result = GlobalSynthesizer().synthesize(
        modal_density=modal,
        peak_classification=peaks,
    )

    assert result.domains[0].recommendation_codes == (
        "MEASURE_MULTIPLE_POSITIONS",
    )
    assert result.domains[1].recommendation_codes == (
        "INVESTIGATE_UNCLASSIFIED_PEAKS",
    )


def test_correlates_stereo_and_sbir_placement_findings():
    result = GlobalSynthesizer().synthesize(
        stereo=StereoAnalysis(symmetry_score=50.0),
        sbir=SBIRAnalysis(score=55.0, confidence=80.0),
    )

    correlation = result.correlations[0]
    assert correlation.code == "STEREO_SBIR_PLACEMENT_INTERACTION"
    assert correlation.domain_codes == ("STEREO", "SBIR")
    assert correlation.source_analyses == ("StereoAnalysis", "SBIRAnalysis")
    assert correlation.score == 50.0


def test_correlates_modal_density_with_physically_classified_modal_peaks():
    result = GlobalSynthesizer().synthesize(
        modal_density=ModalDensityAnalysis(score=65.0, confidence=80.0),
        peak_classification=PeakClassificationAnalysis(
            score=70.0,
            confidence=75.0,
            classifications=[Classification("ROOM_MODE")],
        ),
    )

    assert [item.code for item in result.correlations] == [
        "MODAL_DENSITY_PEAK_INTERACTION"
    ]


def test_does_not_create_a_correlation_without_two_supporting_findings():
    result = GlobalSynthesizer().synthesize(
        stereo=StereoAnalysis(symmetry_score=95.0),
        sbir=SBIRAnalysis(score=55.0, confidence=80.0),
    )

    assert result.correlations == []


def test_uses_local_confidences_when_no_global_confidence_is_available():
    modal = ModalDensityAnalysis(score=70.0, confidence=80.0)
    peaks = PeakClassificationAnalysis(score=90.0, confidence=60.0)

    result = GlobalSynthesizer().synthesize(
        modal_density=modal,
        peak_classification=peaks,
    )

    assert result.confidence == 70.0


def test_returns_an_explicit_empty_result_without_available_domains():
    result = GlobalSynthesizer().synthesize()

    assert result.score is None
    assert result.confidence is None
    assert result.domains == []
    assert result.correlations == []
    assert result.priority_domains == ()
    assert result.source_analyses == ()

