from dataclasses import dataclass
from enum import Enum

from acousticbrain.analysis import RecommendationEngine
from acousticbrain.models import (
    ModalBand,
    ModalDensityAnalysis,
    Peak,
    RecommendationPriority,
    ReflectionSurface,
    SBIRAnalysis,
    SBIRCandidate,
    StereoAnalysis,
)


class ClassificationType(Enum):
    UNCLASSIFIED = "UNCLASSIFIED"


@dataclass
class Classification:
    classification: ClassificationType


@dataclass
class PeakClassificationAnalysis:
    classifications: list[Classification]
    confidence: float


@dataclass
class ConfidenceAnalysis:
    score: float


def test_recommends_checking_an_asymmetric_stereo_placement():
    peak = Peak(frequency=80.0, spl=85.0, index=0, prominence=10.0)
    analysis = StereoAnalysis(left_only_peaks=[peak])

    result = RecommendationEngine().analyze(stereo=analysis)

    assert [item.code for item in result.recommendations] == [
        "CHECK_STEREO_PLACEMENT"
    ]
    assert result.recommendations[0].source_analyses == ("StereoAnalysis",)


def test_recommends_testing_distance_for_an_sbir_match():
    peak = Peak(frequency=70.0, spl=70.0, index=0, prominence=8.0)
    candidate = SBIRCandidate(
        surface=ReflectionSurface.FRONT_WALL,
        measured_frequency=70.0,
        theoretical_frequency=72.0,
        distance_m=1.2,
        delay_ms=7.0,
        frequency_error_hz=2.0,
        match_score=80.0,
        peak=peak,
    )
    analysis = SBIRAnalysis(
        candidates=[candidate],
        best_match=candidate,
        reflection_surface=ReflectionSurface.FRONT_WALL,
        reflection_distance_m=1.2,
        delay_ms=7.0,
        confidence=82.0,
        score=55.0,
    )

    recommendation = RecommendationEngine().analyze(sbir=analysis).recommendations[0]

    assert recommendation.code == "TEST_SPEAKER_DISTANCE"
    assert recommendation.priority is RecommendationPriority.HIGH
    assert recommendation.parameters["current_distance_m"] == 1.2


def test_deduplicates_actions_and_combines_their_analysis_provenance():
    band = ModalBand(40.0, 80.0, 1, 0.025, None)
    modal = ModalDensityAnalysis(
        sparse_bands=[band],
        score=70.0,
        confidence=75.0,
    )
    peaks = PeakClassificationAnalysis(
        classifications=[Classification(ClassificationType.UNCLASSIFIED)],
        confidence=80.0,
    )

    result = RecommendationEngine().analyze(
        modal_density=modal,
        peak_classification=peaks,
    )

    measurements = [
        item for item in result.recommendations
        if item.code == "MEASURE_MULTIPLE_POSITIONS"
    ]
    assert len(measurements) == 1
    assert measurements[0].source_analyses == (
        "ModalDensityAnalysis",
        "PeakClassificationAnalysis",
    )
    assert measurements[0].confidence == 80.0


def test_global_confidence_can_only_lower_recommendation_confidence():
    peak = Peak(frequency=80.0, spl=85.0, index=0, prominence=10.0)
    stereo = StereoAnalysis(left_only_peaks=[peak])

    recommendation = RecommendationEngine().analyze(
        stereo=stereo,
        confidence=ConfidenceAnalysis(score=45.0),
    ).recommendations[0]

    assert recommendation.confidence == 45.0


def test_global_confidence_never_creates_a_recommendation():
    result = RecommendationEngine().analyze(
        confidence=ConfidenceAnalysis(score=100.0)
    )

    assert result.recommendations == []


def test_returns_only_an_empty_recommendation_analysis_without_useful_facts():
    result = RecommendationEngine().analyze(stereo=StereoAnalysis())

    assert result.recommendations == []
