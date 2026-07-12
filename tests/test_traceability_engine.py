from dataclasses import dataclass, field
from types import SimpleNamespace

from acousticbrain.analysis import TraceabilityEngine
from acousticbrain.models import EvidenceLevel


@dataclass
class Domain:
    code: str
    score: float
    source_analysis: str


@dataclass
class Correlation:
    code: str
    source_analyses: tuple[str, ...]


@dataclass
class GlobalAnalysis:
    domains: list[Domain] = field(default_factory=list)
    correlations: list[Correlation] = field(default_factory=list)
    source_analyses: tuple[str, ...] = ()


@dataclass
class Recommendation:
    code: str
    source_analyses: tuple[str, ...]


@dataclass
class RecommendationAnalysis:
    recommendations: list[Recommendation] = field(default_factory=list)


@dataclass
class ConfidenceAnalysis:
    score: float


def structured_inputs():
    global_analysis = GlobalAnalysis(
        domains=[
            Domain("STEREO", 50.0, "StereoAnalysis"),
            Domain("SBIR", 55.0, "SBIRAnalysis"),
        ],
        correlations=[
            Correlation(
                "STEREO_SBIR_PLACEMENT_INTERACTION",
                ("StereoAnalysis", "SBIRAnalysis"),
            )
        ],
        source_analyses=("StereoAnalysis", "SBIRAnalysis"),
    )
    recommendations = RecommendationAnalysis(
        [
            Recommendation(
                "TEST_SPEAKER_DISTANCE",
                ("StereoAnalysis", "SBIRAnalysis"),
            )
        ]
    )
    return global_analysis, recommendations


def test_builds_deterministic_evidence_from_existing_global_domains():
    global_analysis, recommendations = structured_inputs()

    result = TraceabilityEngine().analyze(
        global_analysis=global_analysis,
        recommendation_analysis=recommendations,
    )

    assert [item.code for item in result.evidence_references] == [
        "evidence.global.domain.stereo.score",
        "evidence.global.domain.sbir.score",
    ]
    assert result.evidence_references[0].fact_code == "global.domain.stereo.score"
    assert result.evidence_references[0].source_analysis == "GlobalAnalysis"
    assert result.evidence_references[0].value == 50.0
    assert result.evidence_references[0].evidence_level is EvidenceLevel.CALCULATED


def test_links_recommendation_to_physical_evidence_and_correlation():
    global_analysis, recommendations = structured_inputs()

    result = TraceabilityEngine().analyze(
        global_analysis=global_analysis,
        recommendation_analysis=recommendations,
    )
    link = next(
        item
        for item in result.links
        if item.recommendation_codes == ("TEST_SPEAKER_DISTANCE",)
    )

    assert link.code == "explanation.recommendation.test_speaker_distance"
    assert link.fact_codes == (
        "global.domain.stereo.score",
        "global.domain.sbir.score",
    )
    assert link.evidence_codes == (
        "evidence.global.domain.stereo.score",
        "evidence.global.domain.sbir.score",
    )
    assert link.correlation_codes == (
        "STEREO_SBIR_PLACEMENT_INTERACTION",
    )


def test_does_not_invent_a_link_for_an_unsupported_recommendation():
    global_analysis, _ = structured_inputs()
    recommendations = RecommendationAnalysis(
        [Recommendation("UNKNOWN_ACTION", ("UnknownAnalysis",))]
    )

    result = TraceabilityEngine().analyze(
        global_analysis=global_analysis,
        recommendation_analysis=recommendations,
    )

    assert all(not link.recommendation_codes for link in result.links)


def test_optional_confidence_is_referenced_without_creating_physical_evidence():
    global_analysis, recommendations = structured_inputs()

    result = TraceabilityEngine().analyze(
        global_analysis=global_analysis,
        recommendation_analysis=recommendations,
        confidence=ConfidenceAnalysis(score=72.0),
    )

    confidence_evidence = result.evidence_references[-1]
    assert confidence_evidence.code == "evidence.global.confidence"
    assert confidence_evidence.value == 72.0
    assert result.links[-1].code == "explanation.global.confidence"


def test_returns_an_empty_graph_when_inputs_contain_no_facts():
    result = TraceabilityEngine().analyze(
        global_analysis=GlobalAnalysis(),
        recommendation_analysis=RecommendationAnalysis(),
    )

    assert result.evidence_references == []
    assert result.links == []
    assert result.source_analyses == (
        "GlobalAnalysis",
        "RecommendationAnalysis",
    )


def expanded_inputs():
    global_analysis = GlobalAnalysis(
        domains=[
            Domain("RT60", 60.0, "RT60Analysis"),
            Domain("ETC", 40.0, "ETCAnalysis"),
            Domain("CLARITY", 50.0, "ClarityAnalysis"),
            Domain("SPATIAL", 40.0, "SpatialAnalysis"),
        ],
        correlations=[
            Correlation(
                "RT60_CLARITY_DECAY_INTERACTION",
                (
                    "RT60Analysis",
                    "ClarityAnalysis",
                    "ClarityCorrelationAnalysis",
                ),
            )
        ],
        source_analyses=(
            "RT60Analysis",
            "ETCAnalysis",
            "ClarityAnalysis",
            "SpatialAnalysis",
        ),
    )
    recommendations = RecommendationAnalysis(
        [
            Recommendation(
                "INVESTIGATE_RT60_CHANNEL_DIFFERENCES",
                ("RT60Analysis",),
            ),
            Recommendation(
                "INVESTIGATE_DOMINANT_EARLY_REFLECTIONS",
                ("ETCAnalysis", "ETCReflectionCorrelationAnalysis"),
            ),
            Recommendation(
                "CHECK_EARLY_REFLECTION_SYMMETRY",
                (
                    "ETCAnalysis",
                    "ClarityAnalysis",
                    "ClarityCorrelationAnalysis",
                ),
            ),
            Recommendation(
                "VERIFY_TIME_ALIGNMENT",
                (
                    "SpatialAnalysis",
                    "ETCAnalysis",
                    "SpatialCorrelationAnalysis",
                ),
            ),
        ]
    )
    rt60 = SimpleNamespace(
        left_right_band_differences=[
            SimpleNamespace(confidence=80.0, difference_seconds=0.4),
            SimpleNamespace(confidence=60.0, difference_seconds=2.0),
        ]
    )
    etc = SimpleNamespace(left_only_event_count=8, right_only_event_count=2)
    clarity = SimpleNamespace(
        left_right_c50_differences_db={1000.0: 3.0},
        left_right_c80_differences_db={},
        left_right_d50_differences_percent={},
        left_right_ts_differences_s={},
    )
    spatial = SimpleNamespace()
    spatial_interpretation = SimpleNamespace(
        technical_center_stability=SimpleNamespace(value="UNSTABLE")
    )
    clarity_correlations = SimpleNamespace(correlations=[object(), object()])
    spatial_correlations = SimpleNamespace(correlations=[object()])
    event = SimpleNamespace(delay_ms=10.0, relative_level_db=-10.0)
    etc_reflections = SimpleNamespace(unmatched_events={"LEFT": [event] * 3})
    return (
        global_analysis,
        recommendations,
        rt60,
        etc,
        clarity,
        spatial,
        spatial_interpretation,
        clarity_correlations,
        spatial_correlations,
        etc_reflections,
    )


def test_links_new_recommendations_and_global_correlation_to_atomic_evidence():
    inputs = expanded_inputs()

    result = TraceabilityEngine().analyze(
        global_analysis=inputs[0],
        recommendation_analysis=inputs[1],
        rt60=inputs[2],
        etc=inputs[3],
        clarity=inputs[4],
        spatial=inputs[5],
        spatial_interpretation=inputs[6],
        clarity_correlations=inputs[7],
        spatial_correlations=inputs[8],
        etc_reflection_correlations=inputs[9],
    )

    evidence = {item.code: item for item in result.evidence_references}
    assert evidence["evidence.rt60.reliable_difference_count"].value == 1
    assert evidence["evidence.etc.channel_specific_event_count"].value == 10
    assert evidence["evidence.clarity.channel_asymmetry_count"].value == 1
    assert evidence["evidence.spatial.technical_center_stability"].value == "UNSTABLE"
    assert evidence["evidence.clarity.correlation_count"].value == 2
    assert evidence["evidence.spatial.correlation_count"].value == 1
    assert evidence[
        "evidence.etc_reflection.dominant_unmatched_event_count"
    ].value == 3
    recommendation_codes = {
        link.recommendation_codes[0]
        for link in result.links
        if link.recommendation_codes
    }
    assert recommendation_codes == {
        "INVESTIGATE_RT60_CHANNEL_DIFFERENCES",
        "INVESTIGATE_DOMINANT_EARLY_REFLECTIONS",
        "CHECK_EARLY_REFLECTION_SYMMETRY",
        "VERIFY_TIME_ALIGNMENT",
    }
    correlation_link = next(
        link
        for link in result.links
        if link.correlation_codes
        == ("RT60_CLARITY_DECAY_INTERACTION",)
    )
    assert "evidence.clarity.correlation_count" in correlation_link.evidence_codes


def test_keeps_new_recommendation_chain_absent_when_one_source_is_missing():
    inputs = expanded_inputs()

    result = TraceabilityEngine().analyze(
        global_analysis=inputs[0],
        recommendation_analysis=inputs[1],
        rt60=inputs[2],
        etc=inputs[3],
        clarity=inputs[4],
        spatial=inputs[5],
        spatial_interpretation=inputs[6],
        clarity_correlations=inputs[7],
        spatial_correlations=None,
        etc_reflection_correlations=inputs[9],
    )

    assert all(
        link.recommendation_codes != ("VERIFY_TIME_ALIGNMENT",)
        for link in result.links
    )


def test_links_drr_recommendation_to_physical_and_correlation_evidence():
    global_analysis = GlobalAnalysis(
        domains=[
            Domain(
                "DIRECT_REVERBERANT",
                30.0,
                "DirectReverberantAnalysis",
            )
        ],
        source_analyses=("DirectReverberantAnalysis",),
    )
    recommendations = RecommendationAnalysis(
        [
            Recommendation(
                "IMPROVE_DIRECT_SOUND_DOMINANCE",
                (
                    "DirectReverberantAnalysis",
                    "DirectReverberantCorrelationAnalysis",
                ),
            )
        ]
    )
    drr = SimpleNamespace(
        broadband_direct_to_reverberant_db=-2.0,
        left_right_direct_to_reverberant_differences_db={1000.0: 4.0},
    )
    correlations = SimpleNamespace(correlations=[object(), object()])

    result = TraceabilityEngine().analyze(
        global_analysis=global_analysis,
        recommendation_analysis=recommendations,
        direct_reverberant=drr,
        direct_reverberant_correlations=correlations,
    )

    evidence_codes = {item.code for item in result.evidence_references}
    assert "evidence.direct_reverberant.broadband_drr_db" in evidence_codes
    assert "evidence.direct_reverberant.correlation_count" in evidence_codes
    link = next(
        item
        for item in result.links
        if item.recommendation_codes
        == ("IMPROVE_DIRECT_SOUND_DOMINANCE",)
    )
    assert link.evidence_codes == (
        "evidence.direct_reverberant.broadband_drr_db",
        "evidence.direct_reverberant.correlation_count",
    )


def test_traces_bass_decay_domain_and_four_separate_physical_facts():
    global_analysis = GlobalAnalysis(
        domains=[Domain("BASS_DECAY", 55.0, "BassDecayAnalysis")],
        source_analyses=("BassDecayAnalysis",),
    )
    recommendations = RecommendationAnalysis(
        [
            Recommendation(
                "COMPARE_BASS_DECAY_CHANNELS",
                ("BassDecayAnalysis", "BassDecayCorrelationAnalysis"),
            )
        ]
    )
    bass = SimpleNamespace(
        aggregate_bands=[
            SimpleNamespace(estimated_decay_time_seconds=1.2),
            SimpleNamespace(estimated_decay_time_seconds=0.9),
        ],
        left_right_band_differences=[
            SimpleNamespace(difference_seconds=0.3),
            SimpleNamespace(difference_seconds=0.1),
        ],
    )
    correlations = SimpleNamespace(correlations=[object(), object()])

    result = TraceabilityEngine().analyze(
        global_analysis=global_analysis,
        recommendation_analysis=recommendations,
        bass_decay=bass,
        bass_decay_correlations=correlations,
    )

    evidence = {item.code: item for item in result.evidence_references}
    domain = evidence["evidence.global.domain.bass_decay.score"]
    assert domain.source_analysis == "GlobalAnalysis"
    assert domain.fact_code == "global.domain.bass_decay.score"
    assert evidence["evidence.bass_decay.usable_band_count"].value == 2
    assert evidence["evidence.bass_decay.maximum_decay_time"].value == 1.2
    assert evidence[
        "evidence.bass_decay.significant_difference_count"
    ].value == 1
    assert evidence["evidence.bass_decay.correlation_count"].value == 2
    link = next(
        item
        for item in result.links
        if item.recommendation_codes == ("COMPARE_BASS_DECAY_CHANNELS",)
    )
    assert link.evidence_codes == (
        "evidence.bass_decay.significant_difference_count",
        "evidence.bass_decay.correlation_count",
    )
