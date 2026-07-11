from dataclasses import dataclass, field

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
        "evidence.stereo.score",
        "evidence.sbir.score",
    ]
    assert result.evidence_references[0].fact_code == "stereo.score"
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
    assert link.fact_codes == ("stereo.score", "sbir.score")
    assert link.evidence_codes == (
        "evidence.stereo.score",
        "evidence.sbir.score",
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
