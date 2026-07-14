from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.models import (
    GlobalAnalysis,
    GlobalCorrelation,
    GlobalDomainAnalysis,
    Measurement,
    Recommendation,
    RecommendationAnalysis,
    RecommendationPriority,
    RecommendationStatus,
)
from acousticbrain.report import ConsoleReporter, GlobalPresenter


class Project:
    name = "Studio"


def global_analysis():
    return GlobalAnalysis(
        score=62.5,
        confidence=71.0,
        domains=[
            GlobalDomainAnalysis(
                code="STEREO",
                score=50.0,
                confidence=None,
                source_analysis="StereoAnalysis",
                recommendation_codes=("CHECK_STEREO_PLACEMENT",),
            ),
            GlobalDomainAnalysis(
                code="SBIR",
                score=75.0,
                confidence=71.0,
                source_analysis="SBIRAnalysis",
            ),
        ],
        correlations=[
            GlobalCorrelation(
                code="STEREO_SBIR_PLACEMENT_INTERACTION",
                domain_codes=("STEREO", "SBIR"),
                source_analyses=("StereoAnalysis", "SBIRAnalysis"),
                score=50.0,
            )
        ],
        priority_domains=("STEREO", "SBIR"),
        source_analyses=("StereoAnalysis", "SBIRAnalysis"),
    )


def test_projects_all_global_fields_without_reordering_or_recalculation():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.global_analysis = global_analysis()

    presented = GlobalPresenter().present(context)

    assert presented.score == 62.5
    assert presented.confidence == 71.0
    assert [domain.code for domain in presented.domains] == ["STEREO", "SBIR"]
    assert presented.domains[0].confidence is None
    assert presented.domains[0].recommendation_codes == (
        "CHECK_STEREO_PLACEMENT",
    )
    assert [item.code for item in presented.correlations] == [
        "STEREO_SBIR_PLACEMENT_INTERACTION"
    ]
    assert presented.priority_domains == ("STEREO", "SBIR")
    assert presented.source_analyses == ("StereoAnalysis", "SBIRAnalysis")


def test_projects_non_active_recommendation_status_into_global_reference():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.global_analysis = global_analysis()
    context.recommendation_analysis = RecommendationAnalysis([Recommendation(
        code="CHECK_STEREO_PLACEMENT",
        action="check_placement",
        target="stereo_speakers",
        priority=RecommendationPriority.HIGH,
        confidence=70.0,
        source_analyses=("StereoAnalysis",),
        status=RecommendationStatus.COMPLETED,
        status_reason="EXPERIMENT_PROTOCOL_COMPLETED",
    )])

    presented = GlobalPresenter().present(context)

    assert presented.domains[0].recommendation_statuses == (
        ("CHECK_STEREO_PLACEMENT", "COMPLETED"),
    )


def test_handles_an_absent_global_analysis_without_fallback_values():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    assert GlobalPresenter().present(context) is None


def test_report_builder_consumes_only_global_analysis():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.global_analysis = global_analysis()

    report = ReportBuilder().build(Project(), context)

    assert report.global_analysis.score == context.global_analysis.score
    assert report.diagnostics == []


def test_console_displays_structured_global_identity(capsys):
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.global_analysis = global_analysis()
    report = ReportBuilder().build(Project(), context)
    report.room_properties = type(
        "RoomProperties",
        (),
        {"volume": 1.0, "floor_area": 1.0, "schroeder_frequency": 100.0},
    )()

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert "Score : 62.5 / 100" in output
    assert "Domaine STEREO" in output
    assert "Confiance : indisponible" in output
    assert "CHECK_STEREO_PLACEMENT" in output
    assert "Corrélation STEREO_SBIR_PLACEMENT_INTERACTION" in output
    assert "Provenances : StereoAnalysis, SBIRAnalysis" in output
