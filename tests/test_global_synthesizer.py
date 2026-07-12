from dataclasses import dataclass, field

import pytest

from acousticbrain.analysis import GlobalSynthesizer
from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayBandAnalysis,
    BassDecayCorrelation,
    BassDecayCorrelationAnalysis,
    DecayUsability,
    ClarityAnalysis,
    ClarityCorrelation,
    ClarityCorrelationAnalysis,
    DirectReverberantAnalysis,
    DirectReverberantCorrelation,
    DirectReverberantCorrelationAnalysis,
    ETCAnalysis,
    ETCReflectionCorrelationAnalysis,
    ImpulseChannel,
    ModalDensityAnalysis,
    RT60Analysis,
    SpatialAnalysis,
    SpatialChannelPairAnalysis,
    SpatialCorrelation,
    SpatialCorrelationAnalysis,
    SpatialMeasurementType,
)


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


def new_analyses():
    rt60 = RT60Analysis(
        broadband_rt60_seconds=0.35,
        interchannel_homogeneity=80.0,
        confidence=94.0,
    )
    etc = ETCAnalysis(
        available_channels=[ImpulseChannel.LEFT],
        common_event_count=10,
        left_only_event_count=2,
        confidence=90.0,
    )
    etc_correlations = ETCReflectionCorrelationAnalysis(
        evaluated_event_count=10,
        matched_event_count=5,
        confidence=80.0,
    )
    clarity = ClarityAnalysis(confidence=88.0)
    clarity_correlations = ClarityCorrelationAnalysis(
        correlations=[
            ClarityCorrelation(
                code="LOW_CLARITY_HIGH_RT60",
                center_frequencies_hz=(1000.0,),
            ),
            ClarityCorrelation(
                code="LOW_CLARITY_DENSE_EARLY_REFLECTIONS",
                center_frequencies_hz=(1000.0,),
            ),
        ]
    )
    pair = SpatialChannelPairAnalysis(
        measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR
    )
    spatial = SpatialAnalysis(
        pair_analysis=pair,
        source_measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        confidence=70.0,
    )
    spatial_correlations = SpatialCorrelationAnalysis(
        correlations=[
            SpatialCorrelation(code="SPATIAL_LEVEL_STEREO_IMBALANCE"),
            SpatialCorrelation(code="SPATIAL_TIME_ETC_CHANNEL_IMBALANCE"),
        ]
    )
    return (
        rt60,
        etc,
        etc_correlations,
        clarity,
        clarity_correlations,
        spatial,
        spatial_correlations,
    )


def test_derives_four_new_domain_scores_from_structured_facts():
    (
        rt60,
        etc,
        etc_correlations,
        clarity,
        clarity_correlations,
        spatial,
        spatial_correlations,
    ) = new_analyses()

    result = GlobalSynthesizer().synthesize(
        rt60=rt60,
        etc=etc,
        clarity=clarity,
        spatial=spatial,
        clarity_correlations=clarity_correlations,
        spatial_correlations=spatial_correlations,
        etc_reflection_correlations=etc_correlations,
    )

    domains = {domain.code: domain for domain in result.domains}
    assert domains["RT60"].score == 94.0
    assert round(domains["ETC"].score, 2) == 62.27
    assert domains["CLARITY"].score == 60.0
    assert domains["SPATIAL"].score == 40.0
    assert domains["RT60"].confidence == 94.0
    assert domains["ETC"].confidence == 80.0
    assert all(not domain.recommendation_codes for domain in domains.values())


def test_omits_new_domains_when_required_facts_are_missing():
    result = GlobalSynthesizer().synthesize(
        rt60=RT60Analysis(confidence=90.0),
        etc=ETCAnalysis(confidence=90.0),
        clarity=ClarityAnalysis(confidence=90.0),
        spatial=SpatialAnalysis(confidence=90.0),
    )

    assert result.domains == []


def test_builds_four_global_correlations_from_lower_structured_correlations():
    (
        rt60,
        etc,
        etc_correlations,
        clarity,
        clarity_correlations,
        spatial,
        spatial_correlations,
    ) = new_analyses()

    result = GlobalSynthesizer().synthesize(
        stereo=StereoAnalysis(symmetry_score=50.0),
        rt60=rt60,
        etc=etc,
        clarity=clarity,
        spatial=spatial,
        clarity_correlations=clarity_correlations,
        spatial_correlations=spatial_correlations,
        etc_reflection_correlations=etc_correlations,
    )

    assert [item.code for item in result.correlations] == [
        "ETC_SPATIAL_ASYMMETRY",
        "RT60_CLARITY_DECAY_INTERACTION",
        "ETC_CLARITY_EARLY_ENERGY_INTERACTION",
        "SPATIAL_STEREO_ALIGNMENT",
    ]
    assert result.correlations[0].source_analyses == (
        "ETCAnalysis",
        "SpatialAnalysis",
        "SpatialCorrelationAnalysis",
    )


def test_does_not_create_new_global_correlation_from_domain_scores_alone():
    (
        rt60,
        etc,
        etc_correlations,
        clarity,
        _,
        spatial,
        _,
    ) = new_analyses()

    result = GlobalSynthesizer().synthesize(
        rt60=rt60,
        etc=etc,
        clarity=clarity,
        spatial=spatial,
        clarity_correlations=ClarityCorrelationAnalysis(),
        spatial_correlations=SpatialCorrelationAnalysis(),
        etc_reflection_correlations=etc_correlations,
    )

    assert result.correlations == []


def test_adds_drr_domain_and_three_supported_global_correlations():
    (
        rt60,
        etc,
        etc_correlations,
        clarity,
        clarity_correlations,
        spatial,
        spatial_correlations,
    ) = new_analyses()
    drr = DirectReverberantAnalysis(
        broadband_direct_to_reverberant_db=-2.0,
        confidence=82.0,
    )
    drr_correlations = DirectReverberantCorrelationAnalysis(
        correlations=[
            DirectReverberantCorrelation(code="LOW_DRR_HIGH_RT60"),
            DirectReverberantCorrelation(
                code="LOW_DRR_DOMINANT_EARLY_REFLECTIONS"
            ),
            DirectReverberantCorrelation(
                code="DRR_SPATIAL_CHANNEL_ASYMMETRY"
            ),
        ]
    )

    result = GlobalSynthesizer().synthesize(
        rt60=rt60,
        etc=etc,
        clarity=clarity,
        spatial=spatial,
        clarity_correlations=clarity_correlations,
        spatial_correlations=spatial_correlations,
        etc_reflection_correlations=etc_correlations,
        direct_reverberant=drr,
        direct_reverberant_correlations=drr_correlations,
    )

    domain = next(
        item for item in result.domains if item.code == "DIRECT_REVERBERANT"
    )
    assert round(domain.score, 2) == 33.33
    assert domain.confidence == 82.0
    codes = {item.code for item in result.correlations}
    assert {
        "LOW_DRR_DECAY_INTERACTION",
        "DRR_EARLY_REFLECTION_INTERACTION",
        "DRR_SPATIAL_ASYMMETRY",
    }.issubset(codes)


def test_drr_domain_aggregates_only_adverse_correlations_without_count_collapse():
    drr = DirectReverberantAnalysis(
        broadband_direct_to_reverberant_db=1.38,
        confidence=90.0,
    )
    correlations = DirectReverberantCorrelationAnalysis(
        correlations=[
            DirectReverberantCorrelation(
                code="LOW_DRR_HIGH_RT60", score=80.0
            ),
            DirectReverberantCorrelation(
                code="DRR_SPATIAL_CHANNEL_ASYMMETRY", score=60.0
            ),
            DirectReverberantCorrelation(
                code="FAVORABLE_DRR_HIGH_CLARITY", score=100.0
            ),
        ]
    )

    result = GlobalSynthesizer().synthesize(
        direct_reverberant=drr,
        direct_reverberant_correlations=correlations,
    )

    # Base large bande 61,5, pénalité moyenne défavorable plafonnée à 30.
    assert result.domains[0].score == 40.5


def test_adds_bass_decay_domain_and_only_supported_global_correlations():
    band = BassDecayBandAnalysis(
        63.0, 56.0, 71.0, -5.0, -25.0, 20.0, 0.4,
        -50.0, 1.2, -45.0, 20.0, -0.98, 80.0,
        "CHANNEL_MEAN", DecayUsability.USABLE,
    )
    bass = BassDecayAnalysis(
        aggregate_bands=[band], coverage=50.0, confidence=80.0
    )
    correlations = BassDecayCorrelationAnalysis(
        correlations=[
            BassDecayCorrelation(code="SLOW_DECAY_RT60_INTERACTION")
        ]
    )
    rt60 = RT60Analysis(
        broadband_rt60_seconds=0.35,
        interchannel_homogeneity=80.0,
        confidence=90.0,
    )

    result = GlobalSynthesizer().synthesize(
        bass_decay=bass,
        bass_decay_correlations=correlations,
        rt60=rt60,
    )

    domain = next(item for item in result.domains if item.code == "BASS_DECAY")
    assert domain.score == pytest.approx(61.6666667)
    assert domain.source_analysis == "BassDecayAnalysis"
    assert [item.code for item in result.correlations] == [
        "BASS_DECAY_RT60_INTERACTION"
    ]
    assert result.correlations[0].source_analyses == (
        "BassDecayAnalysis",
        "RT60Analysis",
        "BassDecayCorrelationAnalysis",
    )
