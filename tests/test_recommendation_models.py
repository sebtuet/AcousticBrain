from dataclasses import asdict, fields

from acousticbrain.models import (
    Recommendation,
    RecommendationAnalysis,
    RecommendationPriority,
)


def test_recommendation_carries_structured_action_and_analysis_provenance():
    recommendation = Recommendation(
        code="adjust_speaker_distance",
        action="move",
        target="left_speaker",
        priority=RecommendationPriority.HIGH,
        confidence=87.5,
        source_analyses=("SBIRAnalysis", "StereoAnalysis"),
        parameters={"distance_m": 0.15, "axis": "depth"},
    )

    assert recommendation.action == "move"
    assert recommendation.parameters["distance_m"] == 0.15
    assert recommendation.source_analyses == ("SBIRAnalysis", "StereoAnalysis")
    assert asdict(recommendation)["priority"] == RecommendationPriority.HIGH


def test_recommendation_priorities_have_a_stable_business_order():
    assert RecommendationPriority.HIGH > RecommendationPriority.MEDIUM
    assert RecommendationPriority.MEDIUM > RecommendationPriority.LOW


def test_recommendation_analysis_defaults_to_an_empty_result():
    assert RecommendationAnalysis().recommendations == []


def test_recommendation_contract_does_not_reference_diagnostics_or_rendering_text():
    field_names = {field.name for field in fields(Recommendation)}

    assert field_names.isdisjoint(
        {
            "diagnostic",
            "diagnostics",
            "title",
            "message",
            "description",
            "justification",
        }
    )

