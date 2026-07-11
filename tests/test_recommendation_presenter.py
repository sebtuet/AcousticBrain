from acousticbrain.analysis import AnalysisContext
from acousticbrain.models import (
    Measurement,
    Recommendation,
    RecommendationAnalysis,
    RecommendationPriority,
)
from acousticbrain.report import RecommendationPresenter


def recommendation(confidence=80.0):
    return Recommendation(
        code="TEST_SPEAKER_DISTANCE",
        action="test_distance",
        target="front_wall",
        priority=RecommendationPriority.HIGH,
        confidence=confidence,
        source_analyses=("SBIRAnalysis", "PeakClassificationAnalysis"),
        parameters={"current_distance_m": 1.2},
    )


def test_projects_every_structured_field_without_recalculation():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    source = recommendation(confidence=12.5)
    context.recommendation_analysis = RecommendationAnalysis([source])

    presented = RecommendationPresenter().present(context)[0]

    assert presented.code == source.code
    assert presented.action == source.action
    assert presented.target == source.target
    assert presented.priority is source.priority
    assert presented.confidence == 12.5
    assert presented.source_analyses == source.source_analyses
    assert presented.parameters == source.parameters


def test_preserves_order_and_duplicates_from_the_engine_result():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    first = recommendation()
    second = recommendation()
    context.recommendation_analysis = RecommendationAnalysis([first, second])

    presented = RecommendationPresenter().present(context)

    assert len(presented) == 2
    assert [item.code for item in presented] == [first.code, second.code]


def test_handles_an_absent_recommendation_analysis():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    assert RecommendationPresenter().present(context) == []
