from dataclasses import dataclass
from enum import Enum
from types import SimpleNamespace

from acousticbrain.analysis import RecommendationEngine
from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayCorrelation,
    BassDecayCorrelationAnalysis,
    ClarityCorrelation,
    ClarityCorrelationAnalysis,
    ETCAnalysis,
    ETCReflectionCorrelationAnalysis,
    DirectReverberantAnalysis,
    DirectReverberantCorrelation,
    DirectReverberantCorrelationAnalysis,
    ImpulseChannel,
    ModalBand,
    ModalDensityAnalysis,
    Peak,
    RecommendationPriority,
    ReflectionSurface,
    ReflectionEvent,
    SBIRAnalysis,
    SBIRCandidate,
    RT60Analysis,
    RT60BandDifference,
    SpatialAnalysis,
    SpatialChannelPairAnalysis,
    SpatialCorrelation,
    SpatialCorrelationAnalysis,
    SpatialMeasurementType,
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


def test_geometry_sbir_match_suppresses_unstructured_legacy_action():
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

    result = RecommendationEngine().analyze(
        sbir=analysis,
        sbir_geometry_correlations=SimpleNamespace(best_match=object()),
    )

    assert result.recommendations == []


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


def test_recommends_investigating_reliable_rt60_channel_differences():
    differences = [
        RT60BandDifference(
            center_frequency_hz=frequency,
            difference_seconds=difference,
            left_rt60_seconds=0.8,
            right_rt60_seconds=0.4,
            confidence=confidence,
            left_estimate="T30",
            right_estimate="T30",
        )
        for frequency, difference, confidence in (
            (63.0, 0.4, 80.0),
            (125.0, 1.2, 75.0),
            (250.0, 0.3, 85.0),
            (500.0, 2.0, 60.0),
        )
    ]

    recommendation = RecommendationEngine().analyze(
        rt60=RT60Analysis(left_right_band_differences=differences)
    ).recommendations[0]

    assert recommendation.code == "INVESTIGATE_RT60_CHANNEL_DIFFERENCES"
    assert recommendation.priority is RecommendationPriority.HIGH
    assert recommendation.confidence == 75.0
    assert recommendation.parameters == {
        "reliable_band_count": 3,
        "maximum_difference_s": 1.2,
    }
    assert recommendation.source_analyses == ("RT60Analysis",)


def test_recommends_treating_only_dominant_unmatched_early_reflections():
    dominant = ReflectionEvent(10.0, -12.0, 0.01, 10, 3.4, 88.0)
    late = ReflectionEvent(30.0, -10.0, 0.03, 30, 10.0, 95.0)
    weak = ReflectionEvent(10.0, -30.0, 0.01, 10, 3.4, 95.0)
    analysis = ETCReflectionCorrelationAnalysis(
        unmatched_events={ImpulseChannel.LEFT: [dominant, late, weak]}
    )

    recommendation = RecommendationEngine().analyze(
        etc_reflection_correlations=analysis
    ).recommendations[0]

    assert recommendation.code == "INVESTIGATE_DOMINANT_EARLY_REFLECTIONS"
    assert recommendation.parameters["important_unmatched_event_count"] == 1
    assert recommendation.confidence == 88.0
    assert recommendation.source_analyses == (
        "ETCAnalysis",
        "ETCReflectionCorrelationAnalysis",
    )


def test_merges_early_reflection_symmetry_support_and_strongest_properties():
    etc = ETCAnalysis(
        left_only_event_count=8,
        right_only_event_count=2,
        confidence=75.0,
    )
    correlations = ClarityCorrelationAnalysis(
        correlations=[
            ClarityCorrelation(
                code="CLARITY_ETC_CHANNEL_ASYMMETRY",
                center_frequencies_hz=(1000.0,),
                confidence=85.0,
            )
        ]
    )

    recommendations = RecommendationEngine().analyze(
        etc=etc,
        clarity_correlations=correlations,
    ).recommendations

    assert len(recommendations) == 1
    recommendation = recommendations[0]
    assert recommendation.code == "CHECK_EARLY_REFLECTION_SYMMETRY"
    assert recommendation.priority is RecommendationPriority.HIGH
    assert recommendation.confidence == 85.0
    assert recommendation.source_analyses == (
        "ETCAnalysis",
        "ClarityAnalysis",
        "ClarityCorrelationAnalysis",
    )


def test_merges_time_alignment_support_without_duplicating_the_action():
    pair = SpatialChannelPairAnalysis(
        measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        broadband_time_difference_ms=0.4,
        confidence=70.0,
    )
    spatial = SpatialAnalysis(
        pair_analysis=pair,
        source_measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        confidence=70.0,
    )
    correlations = SpatialCorrelationAnalysis(
        correlations=[
            SpatialCorrelation(
                code="SPATIAL_TIME_ETC_CHANNEL_IMBALANCE",
                confidence=82.0,
            )
        ]
    )

    recommendations = RecommendationEngine().analyze(
        spatial=spatial,
        spatial_correlations=correlations,
    ).recommendations

    assert len(recommendations) == 1
    recommendation = recommendations[0]
    assert recommendation.code == "VERIFY_TIME_ALIGNMENT"
    assert recommendation.priority is RecommendationPriority.HIGH
    assert recommendation.confidence == 82.0
    assert recommendation.source_analyses == (
        "SpatialAnalysis",
        "ETCAnalysis",
        "SpatialCorrelationAnalysis",
    )


def test_new_analyses_without_required_facts_create_no_action():
    result = RecommendationEngine().analyze(
        rt60=RT60Analysis(),
        etc=ETCAnalysis(),
        spatial=SpatialAnalysis(),
        clarity_correlations=ClarityCorrelationAnalysis(),
        spatial_correlations=SpatialCorrelationAnalysis(),
        etc_reflection_correlations=ETCReflectionCorrelationAnalysis(),
    )

    assert result.recommendations == []


def test_creates_and_deduplicates_drr_actions_from_facts_and_correlations():
    drr = DirectReverberantAnalysis(
        broadband_direct_to_reverberant_db=-2.0,
        left_right_direct_to_reverberant_differences_db={1000.0: 4.0},
        confidence=75.0,
    )
    correlations = DirectReverberantCorrelationAnalysis(
        correlations=[
            DirectReverberantCorrelation(
                code="LOW_DRR_DOMINANT_EARLY_REFLECTIONS",
                confidence=85.0,
            )
        ]
    )

    recommendations = RecommendationEngine().analyze(
        direct_reverberant=drr,
        direct_reverberant_correlations=correlations,
    ).recommendations

    assert {item.code for item in recommendations} == {
        "IMPROVE_DIRECT_SOUND_DOMINANCE",
        "INVESTIGATE_DRR_CHANNEL_DIFFERENCES",
        "APPLY_EARLY_REFLECTION_TREATMENT",
    }
    improve = next(
        item
        for item in recommendations
        if item.code == "IMPROVE_DIRECT_SOUND_DOMINANCE"
    )
    assert improve.confidence == 85.0
    assert improve.source_analyses == (
        "DirectReverberantAnalysis",
        "DirectReverberantCorrelationAnalysis",
    )


def test_creates_stable_bass_decay_actions_from_structured_correlations():
    bass = BassDecayAnalysis(confidence=84.0)
    correlations = BassDecayCorrelationAnalysis(
        correlations=[
            BassDecayCorrelation(
                code="SLOW_DECAY_MODAL_INTERACTION",
                source_metrics={
                    "maximum_decay_time_s": 1.2,
                    "matched_mode_count": 2.0,
                },
                confidence=82.0,
            ),
            BassDecayCorrelation(
                code="ASYMMETRIC_BASS_DECAY",
                source_metrics={
                    "asymmetric_band_count": 2.0,
                    "maximum_left_right_difference_s": 0.4,
                },
                confidence=78.0,
            ),
        ]
    )

    result = RecommendationEngine().analyze(
        bass_decay=bass,
        bass_decay_correlations=correlations,
    )

    assert [item.code for item in result.recommendations] == [
        "INVESTIGATE_LONG_BASS_DECAY",
        "CHECK_MODAL_EXCITATION",
        "COMPARE_BASS_DECAY_CHANNELS",
    ]
    assert result.recommendations[0].parameters == {
        "supporting_correlation_count": 1,
        "maximum_decay_time_s": 1.2,
    }
    assert result.recommendations[2].parameters[
        "maximum_difference_s"
    ] == 0.4
