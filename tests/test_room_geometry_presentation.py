import pytest

from acousticbrain.analysis import AnalysisContext, TraceabilityEngine
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.brain.stages.room_geometry import RoomGeometryStage
from acousticbrain.models import (
    GlobalAnalysis,
    Measurement,
    RecommendationAnalysis,
    Room,
    RoomDescription,
    RoomDimensions,
)
from acousticbrain.project import Project
from acousticbrain.report import ConsoleReporter, RoomGeometryPresenter


def context_for(project):
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    RoomGeometryStage().run(project, context)
    return context


def test_presenter_exposes_resolved_geometry_identity():
    context = context_for(Project("Project", Room("Legacy", 5.84, 5.51, 2.60)))

    presented = RoomGeometryPresenter().present(context)

    assert presented.source == "LEGACY_ROOM"
    assert presented.model == "RECTANGULAR"
    assert presented.model_version == 1
    assert (presented.length_m, presented.width_m, presented.height_m) == (
        5.84,
        5.51,
        2.60,
    )
    assert presented.completeness == 60.0
    assert presented.comparison_status == "SINGLE_SOURCE"


def test_console_warns_only_when_declared_and_legacy_dimensions_diverge(capsys):
    equivalent = Project(
        "Equivalent",
        Room("Legacy", 5.0, 4.0, 2.5),
        room_description=RoomDescription(
            "Declared", RoomDimensions(5.0, 4.0, 2.5)
        ),
    )
    equivalent_context = context_for(equivalent)
    equivalent_report = ReportBuilder().build(equivalent, equivalent_context)

    ConsoleReporter().print(equivalent_report)
    output = capsys.readouterr().out

    assert "Source : ROOM_DESCRIPTION" in output
    assert "Modèle : RECTANGULAR" in output
    assert "Dimensions : 5.00 × 4.00 × 2.50 m" in output
    assert "Compatibilité des sources : EQUIVALENT" in output
    assert "Avertissement" not in output

    divergent = Project(
        "Divergent",
        Room("Legacy", 5.0, 4.0, 2.5),
        room_description=RoomDescription(
            "Declared", RoomDimensions(6.0, 4.0, 2.7)
        ),
    )
    divergent_context = context_for(divergent)
    divergent_report = ReportBuilder().build(divergent, divergent_context)

    ConsoleReporter().print(divergent_report)
    output = capsys.readouterr().out

    assert "Compatibilité des sources : DIVERGENT" in output
    assert "Avertissement" in output
    assert "length_m, height_m" in output


def test_traceability_preserves_geometry_provenance_and_divergence_facts():
    project = Project(
        "Divergent",
        Room("Legacy", 5.0, 4.0, 2.5),
        room_description=RoomDescription(
            "Declared", RoomDimensions(6.0, 4.0, 2.7)
        ),
    )
    context = context_for(project)

    traceability = TraceabilityEngine().analyze(
        global_analysis=GlobalAnalysis(),
        recommendation_analysis=RecommendationAnalysis(),
        room_geometry=context.room_geometry,
        room_geometry_comparison=context.room_geometry_comparison,
    )
    evidence = {item.fact_code: item for item in traceability.evidence_references}

    assert evidence["room_geometry.source"].value == "ROOM_DESCRIPTION"
    assert evidence["room_geometry.model"].value == "RECTANGULAR"
    assert evidence["room_geometry.model_version"].value == 1
    assert evidence["room_geometry.completeness"].value == 60.0
    assert evidence["room_geometry.comparison_status"].value == "DIVERGENT"
    assert evidence["room_geometry.difference.length_m"].value == 1.0
    assert evidence["room_geometry.difference.height_m"].value == pytest.approx(0.2)
    assert "RoomGeometry" in traceability.source_analyses


def test_presenter_returns_none_before_geometry_resolution():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    assert RoomGeometryPresenter().present(context) is None
