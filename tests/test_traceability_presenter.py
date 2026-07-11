import json

from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.models import (
    EvidenceLevel,
    EvidenceReference,
    ExplanationLink,
    Measurement,
    TraceabilityAnalysis,
)
from acousticbrain.report import ConsoleReporter, TraceabilityPresenter


class Project:
    name = "Studio"


def traceability_analysis():
    return TraceabilityAnalysis(
        evidence_references=[
            EvidenceReference(
                code="evidence.sbir.score",
                source_analysis="SBIRAnalysis",
                fact_code="sbir.score",
                evidence_level=EvidenceLevel.CALCULATED,
                value=55.0,
            )
        ],
        links=[
            ExplanationLink(
                code="explanation.recommendation.test_speaker_distance",
                fact_codes=("sbir.score",),
                evidence_codes=("evidence.sbir.score",),
                correlation_codes=("STEREO_SBIR_PLACEMENT_INTERACTION",),
                recommendation_codes=("TEST_SPEAKER_DISTANCE",),
            )
        ],
        source_analyses=("GlobalAnalysis", "RecommendationAnalysis"),
    )


def test_projects_the_complete_graph_without_resolving_links():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.traceability_analysis = traceability_analysis()

    presented = TraceabilityPresenter().present(context)

    evidence = presented.evidence_references[0]
    assert evidence.code == "evidence.sbir.score"
    assert evidence.source_analysis == "SBIRAnalysis"
    assert evidence.fact_code == "sbir.score"
    assert evidence.evidence_level == "CALCULATED"
    assert evidence.value == 55.0
    assert presented.links[0].recommendation_codes == (
        "TEST_SPEAKER_DISTANCE",
    )
    assert presented.source_analyses == (
        "GlobalAnalysis",
        "RecommendationAnalysis",
    )


def test_projection_is_directly_json_serializable():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.traceability_analysis = traceability_analysis()

    payload = TraceabilityPresenter().present(context).to_dict()
    encoded = json.dumps(payload)

    assert '"evidence_level": "CALCULATED"' in encoded
    assert '"TEST_SPEAKER_DISTANCE"' in encoded


def test_handles_an_absent_traceability_analysis_without_fallback_graph():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    assert TraceabilityPresenter().present(context) is None


def test_report_builder_consumes_only_traceability_analysis():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.traceability_analysis = traceability_analysis()

    report = ReportBuilder().build(Project(), context)

    assert report.traceability_analysis.links[0].code == (
        "explanation.recommendation.test_speaker_distance"
    )
    assert report.diagnostics == []


def test_console_preserves_stable_graph_identifiers(capsys):
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.traceability_analysis = traceability_analysis()
    report = ReportBuilder().build(Project(), context)
    report.room_properties = type(
        "RoomProperties",
        (),
        {"volume": 1.0, "floor_area": 1.0, "schroeder_frequency": 100.0},
    )()

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert "Preuve evidence.sbir.score" in output
    assert "Niveau : CALCULATED" in output
    assert "Lien explanation.recommendation.test_speaker_distance" in output
    assert "Recommandations : TEST_SPEAKER_DISTANCE" in output

