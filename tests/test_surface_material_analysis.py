from types import SimpleNamespace

from acousticbrain.analysis import (
    AnalysisContext,
    RoomGeometryBuilder,
    SurfaceMaterialAnalyzer,
)
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.brain.stages.propagation_geometry import PropagationGeometryStage
from acousticbrain.brain.stages.surface_material import SurfaceMaterialStage
from acousticbrain.models import (
    Measurement,
    RoomDescription,
    RoomDescriptionPersistenceErrorCode,
    RoomDimensions,
    SurfaceMaterialAssignment,
    SurfaceMaterialCoefficient,
    SurfaceMaterialDescription,
    SurfaceMaterialPrecision,
    SurfaceMaterialQuality,
    SurfaceMaterialSource,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec
from acousticbrain.report import ConsoleReporter, SurfaceMaterialPresenter
from acousticbrain.ui import RoomDescriptionEditorAdapter


def description(assign=True, reverse=False):
    material = SurfaceMaterialDescription(
        "panel", "Panel",
        absorption_coefficients=(SurfaceMaterialCoefficient(125, 0.5),),
        diffusion_coefficients=(),
        source=SurfaceMaterialSource.MEASURED,
        confidence=88,
        quality=SurfaceMaterialQuality.VERIFIED,
        precision=SurfaceMaterialPrecision.OCTAVE,
        provenance_codes=("MEASUREMENT-1",),
    )
    assignments = (
        SurfaceMaterialAssignment("front-panel", "panel", surface_id="front_wall"),
    ) if assign else ()
    return RoomDescription(
        "room", RoomDimensions(5, 4, 3),
        materials=(material,), material_assignments=assignments,
    )


def build(description):
    context = AnalysisContext(Measurement("stereo"))
    context.room_geometry = RoomGeometryBuilder().from_description(description)
    project = SimpleNamespace(
        name="materials",
        room_description=description,
        propagation_geometry=None,
        surface_material_analysis=None,
    )
    PropagationGeometryStage().run(project, context)
    SurfaceMaterialStage().run(project, context)
    return project, context


def test_analysis_exposes_declared_facts_and_provenance_only():
    _, context = build(description())
    analysis = context.surface_material_analysis

    assert analysis.available_material_ids == ("panel",)
    assert "surface_material.panel.absorption.125_hz" in analysis.available_fact_codes
    front = next(item for item in analysis.target_availability if item.target_id == "front_wall")
    assert front.provenance_codes == ("MEASUREMENT-1",)
    assert "SURFACE_MATERIALS_NO_INFERENCE" in analysis.applied_rule_codes


def test_completeness_counts_assigned_geometry_targets_without_interpretation():
    _, context = build(description())
    assert context.surface_material_analysis.completeness == 100 / 6


def test_unassigned_targets_remain_explicitly_missing():
    _, context = build(description(assign=False))
    analysis = context.surface_material_analysis
    assert analysis.completeness == 0
    assert len(analysis.missing_material_target_codes) == 6


def test_absent_frequency_properties_remain_missing_facts():
    _, context = build(description())
    assert "surface_material.panel.diffusion" in context.surface_material_analysis.missing_fact_codes
    assert "surface_material.panel.transmission" in context.surface_material_analysis.missing_fact_codes


def test_missing_propagation_geometry_is_reported_without_fallback():
    analysis = SurfaceMaterialAnalyzer().analyze(description(), None)
    assert analysis.target_availability == ()
    assert analysis.completeness == 0
    assert "propagation_geometry" in analysis.missing_fact_codes


def test_stage_stores_the_same_immutable_analysis_on_project_and_context():
    project, context = build(description())
    assert project.surface_material_analysis is context.surface_material_analysis


def test_presenter_is_absent_for_legacy_or_empty_material_catalogs():
    context = SimpleNamespace(
        surface_material_analysis=SurfaceMaterialAnalyzer().analyze(
            RoomDescription("room", RoomDimensions(5, 4, 3)), None
        )
    )
    assert SurfaceMaterialPresenter().present(context) is None


def test_report_contains_a_factual_surface_material_section(capsys):
    project, context = build(description())
    report = ReportBuilder().build(project, context)

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert "Surface materials" in output
    assert "Material: panel — Panel" in output
    assert "Absorption: 125 Hz=0.500" in output
    assert "Hypoth" not in output.split("Surface materials", 1)[1].split("Assignments:", 1)[0]


def test_propagation_geometry_carries_references_without_material_coefficients():
    _, context = build(description())
    reference = context.propagation_geometry.material_references[0]
    assert reference.material_id == "panel"
    assert reference.surface_id == "front_wall"
    assert not hasattr(reference, "absorption_coefficients")


def test_legacy_editor_refuses_frequency_material_data_instead_of_losing_it():
    payload = RoomDescriptionJsonCodec().dumps(description())
    loaded = RoomDescriptionEditorAdapter().load(payload)

    assert loaded.errors[0].code is (
        RoomDescriptionPersistenceErrorCode.EDITOR_UNSUPPORTED_FREQUENCY_MATERIALS
    )
