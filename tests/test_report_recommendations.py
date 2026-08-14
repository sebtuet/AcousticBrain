from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.models import (
    Measurement,
    Recommendation,
    RecommendationAnalysis,
    RecommendationPriority,
)
from acousticbrain.report import ConsoleReporter


class Project:
    name = "Studio"


def test_report_builder_consumes_only_the_structured_recommendation_analysis():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.recommendation_analysis = RecommendationAnalysis(
        [
            Recommendation(
                code="CHECK_STEREO_PLACEMENT",
                action="check_placement",
                target="stereo_speakers",
                priority=RecommendationPriority.MEDIUM,
                confidence=70.0,
                source_analyses=("StereoAnalysis",),
            )
        ]
    )

    report = ReportBuilder().build(Project(), context)

    assert [item.code for item in report.recommendations] == [
        "CHECK_STEREO_PLACEMENT"
    ]
    assert report.diagnostics == []


def test_console_keeps_structured_identity_and_uncertain_confidence(capsys):
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.recommendation_analysis = RecommendationAnalysis(
        [
            Recommendation(
                code="INVESTIGATE_UNCLASSIFIED_PEAKS",
                action="investigate",
                target="unclassified_peaks",
                priority=RecommendationPriority.MEDIUM,
                confidence=12.5,
                source_analyses=("PeakClassificationAnalysis",),
                parameters={"unclassified_peak_count": 2},
            )
        ]
    )
    report = ReportBuilder().build(Project(), context)
    report.room_properties = type(
        "RoomProperties",
        (),
        {"volume": 1.0, "floor_area": 1.0, "schroeder_frequency": 100.0},
    )()

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert "INVESTIGATE_UNCLASSIFIED_PEAKS" in output
    assert "Action : investigate" in output
    assert "Cible : unclassified_peaks" in output
    assert "Priorité : MEDIUM" in output
    assert "Confiance : 12.5%" in output
    assert "Provenance : PeakClassificationAnalysis" in output
