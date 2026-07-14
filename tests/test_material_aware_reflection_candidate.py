from dataclasses import fields, replace
from inspect import getsource, signature
from pathlib import Path
from types import SimpleNamespace

import pytest

from acousticbrain.analysis import ReflectionCandidateCompatibilityEngine
from acousticbrain.analysis import AnalysisContext, TraceabilityEngine
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.brain.pipeline import BrainPipeline
from acousticbrain.brain.stages.material_aware_reflection_candidate import (
    MaterialAwareReflectionCandidateStage,
)
from acousticbrain.models import (
    ETCReflectionCorrelation,
    ETCReflectionCorrelationAnalysis,
    GeometryCoordinate,
    GeometryEarlyReflectionAnalysis,
    GeometryReflectionPath,
    ImpulseChannel,
    Measurement,
    MaterialAssessment,
    MaterialAwareReflectionCandidateAnalysis,
    ReflectionCandidateAssessment,
    ReflectionCandidateCausalityStatus,
    ReflectionCandidateEligibilityImpact,
    ReflectionCandidateGeometricStatus,
    ReflectionCandidateStatus,
    ReflectionEvent,
    ReflectionSurface,
    SurfaceMaterialAnalysis,
    SurfaceMaterialAssignment,
    SurfaceMaterialCoefficient,
    SurfaceMaterialDescription,
    SurfaceMaterialDescriptionSource,
    SurfaceMaterialPrecision,
    SurfaceMaterialQuality,
    SurfaceMaterialSource,
    SurfaceMaterialTargetAvailability,
)
from acousticbrain.report import (
    ConsoleReporter,
    MaterialAwareReflectionCandidatePresenter,
)


def path(path_id="path.front", *, surface_id="front_wall", base="front_wall"):
    return GeometryReflectionPath(
        path_id=path_id,
        speaker_id="LEFT",
        listening_position_id="MIC",
        surface_id=surface_id,
        base_surface_id=base,
        surface=ReflectionSurface.FRONT_WALL,
        impact_point=GeometryCoordinate(0.0, 1.0, 1.0),
        direct_path_m=2.0,
        reflected_path_m=3.0,
        acoustic_path_difference_m=1.0,
        theoretical_delay_ms=2.9,
        uncertainty_ms=0.2,
        confidence=88.0,
        provenance_codes=("GEOMETRY-SOURCE",),
    )


def correlation(item, *, code="correlation.front", score=90.0, sample=144):
    event = ReflectionEvent(3.0, -8.0, 0.003, sample, 1.029, 92.0)
    return ETCReflectionCorrelation(
        code=code,
        channel=ImpulseChannel.LEFT,
        event=event,
        surface=item.surface,
        theoretical_delay_ms=item.theoretical_delay_ms,
        measured_delay_ms=event.delay_ms,
        timing_error_ms=abs(event.delay_ms - item.theoretical_delay_ms),
        acoustic_path_difference_m=event.acoustic_path_difference_m,
        match_score=score,
        confidence=90.0,
        source_analyses=("ETCAnalysis", "GeometryEarlyReflectionAnalysis"),
        surface_id=item.surface_id,
        impact_point=item.impact_point,
        geometric_uncertainty_ms=item.uncertainty_ms,
        geometry_confidence=item.confidence,
        geometry_path_id=item.path_id,
        provenance_codes=("CORRELATION-SOURCE",),
    )


def materials(
    absorption=None,
    *,
    target_kind="SURFACE",
    target_id="front_wall",
    catalog_entry_id="catalog:panel:v1",
):
    if absorption is None:
        return SurfaceMaterialAnalysis(
            materials=(), assignments=(),
            target_availability=(SurfaceMaterialTargetAvailability(
                target_kind, target_id, None
            ),),
            available_material_ids=(),
            missing_material_target_codes=(f"MATERIAL_MISSING.{target_kind}.{target_id}",),
            completeness=0.0,
            available_fact_codes=(), missing_fact_codes=(),
            source_analysis_codes=("RoomDescription", "PropagationGeometryAnalysis"),
            applied_rule_codes=("SURFACE_MATERIALS_NO_INFERENCE",),
        )
    material = SurfaceMaterialDescription(
        "panel", "Panel",
        absorption_coefficients=tuple(
            SurfaceMaterialCoefficient(frequency, coefficient)
            for frequency, coefficient in absorption
        ),
        diffusion_coefficients=(),
        source=SurfaceMaterialSource.CATALOG_ESTIMATE,
        confidence=82.0,
        quality=SurfaceMaterialQuality.ESTIMATED,
        precision=SurfaceMaterialPrecision.OCTAVE,
        provenance_codes=("MATERIAL-SOURCE",),
        catalog_entry_id=catalog_entry_id,
    )
    assignment = SurfaceMaterialAssignment(
        "assignment.panel", "panel",
        surface_id=target_id if target_kind == "SURFACE" else None,
        region_id=target_id if target_kind == "REGION" else None,
        description_source=(
            SurfaceMaterialDescriptionSource.USER_STRUCTURED_INPUT
        ),
        description_confidence=76.0,
        provenance_codes=("ASSIGNMENT-SOURCE",),
    )
    return SurfaceMaterialAnalysis(
        materials=(material,), assignments=(assignment,),
        target_availability=(SurfaceMaterialTargetAvailability(
            target_kind, target_id, "panel",
            provenance_codes=("MATERIAL-SOURCE",),
            description_provenance_codes=("ASSIGNMENT-SOURCE",),
            description_source="USER_STRUCTURED_INPUT",
            description_confidence=76.0,
        ),),
        available_material_ids=("panel",), missing_material_target_codes=(),
        completeness=100.0, available_fact_codes=("material.panel",),
        missing_fact_codes=(),
        source_analysis_codes=("RoomDescription", "PropagationGeometryAnalysis"),
        applied_rule_codes=("SURFACE_MATERIALS_NO_INFERENCE",),
    )


def analyze(material_analysis=None, *, paths=None, correlations=None):
    paths = paths or (path(),)
    correlations = correlations if correlations is not None else (
        correlation(paths[0]),
    )
    return ReflectionCandidateCompatibilityEngine().analyze(
        GeometryEarlyReflectionAnalysis(
            tuple(paths), ("RoomGeometry",), ("IMAGE_SOURCE",)
        ),
        ETCReflectionCorrelationAnalysis(correlations=list(correlations)),
        material_analysis or materials(None),
    )


def accepted(result):
    return next(
        item for item in result.candidates
        if item.geometric_status is ReflectionCandidateGeometricStatus.ACCEPTED
    )


def test_engine_signature_contains_exactly_three_source_analyses():
    assert tuple(signature(ReflectionCandidateCompatibilityEngine.analyze).parameters) == (
        "self", "geometry_analysis", "correlation_analysis", "material_analysis"
    )


def test_analysis_declares_exactly_three_upstream_sources():
    assert analyze().source_analysis_codes == (
        "GeometryEarlyReflectionAnalysis",
        "ETCReflectionCorrelationAnalysis",
        "SurfaceMaterialAnalysis",
    )


@pytest.mark.parametrize(
    ("coefficients", "expected", "factor"),
    [
        (None, MaterialAssessment.UNKNOWN, 1.0),
        ((), MaterialAssessment.UNKNOWN, 1.0),
        (((125, 0.10),), MaterialAssessment.COMPATIBLE, 1.0),
        (((125, 0.35),), MaterialAssessment.COMPATIBLE, 1.0),
        (((125, 0.36),), MaterialAssessment.WEAKLY_INCOMPATIBLE, 0.85),
        (((125, 0.65),), MaterialAssessment.WEAKLY_INCOMPATIBLE, 0.85),
        (((125, 0.66),), MaterialAssessment.INCOMPATIBLE, 0.60),
        (((125, 1.00),), MaterialAssessment.INCOMPATIBLE, 0.60),
        (((125, 0.2), (250, 0.4)), MaterialAssessment.COMPATIBLE, 1.0),
        (((125, 0.4), (250, 0.6)), MaterialAssessment.WEAKLY_INCOMPATIBLE, 0.85),
        (((125, 0.7), (250, 0.9)), MaterialAssessment.INCOMPATIBLE, 0.60),
    ],
)
def test_material_assessment_is_bounded_and_secondary(coefficients, expected, factor):
    result = analyze(materials(coefficients))
    item = accepted(result)
    assert item.material_assessment is expected
    assert item.overall_compatibility_score == pytest.approx(
        item.geometric_temporal_score * factor
    )
    assert 0 <= item.overall_compatibility_score <= item.geometric_temporal_score


def test_unknown_material_is_exactly_score_neutral():
    item = accepted(analyze(materials(None)))
    assert item.material_assessment is MaterialAssessment.UNKNOWN
    assert item.overall_compatibility_score == item.geometric_temporal_score


@pytest.mark.parametrize("score", [0.0, 1.0, 50.0, 99.999, 100.0])
def test_unknown_material_neutrality_holds_for_all_geometric_scores(score):
    item_path = path()
    item = accepted(analyze(
        materials(None),
        paths=(item_path,),
        correlations=(correlation(item_path, score=score),),
    ))
    assert item.overall_compatibility_score == score


def test_unmatched_geometry_path_remains_rejected_without_rank():
    result = analyze(paths=(path(),), correlations=())
    item = result.candidates[0]
    assert item.geometric_status is ReflectionCandidateGeometricStatus.REJECTED
    assert item.status is ReflectionCandidateStatus.REJECTED
    assert item.informative_rank is None
    assert item.overall_compatibility_score == 0.0


def test_known_material_cannot_rehabilitate_rejected_path():
    item = analyze(materials(((125, 0.1),)), correlations=()).candidates[0]
    assert item.material_assessment is MaterialAssessment.COMPATIBLE
    assert item.status is ReflectionCandidateStatus.REJECTED


def test_region_assignment_has_priority_over_base_surface_assignment():
    region_path = path(surface_id="panel-region", base="front_wall")
    item = accepted(analyze(
        materials(((125, 0.8),), target_kind="REGION", target_id="panel-region"),
        paths=(region_path,), correlations=(correlation(region_path),),
    ))
    assert item.surface_id == "front_wall"
    assert item.region_id == "panel-region"
    assert item.assignment_id == "assignment.panel"
    assert item.material_assessment is MaterialAssessment.INCOMPATIBLE


def test_region_without_assignment_falls_back_to_declared_base_surface():
    region_path = path(surface_id="panel-region", base="front_wall")
    item = accepted(analyze(
        materials(((125, 0.1),), target_kind="SURFACE", target_id="front_wall"),
        paths=(region_path,), correlations=(correlation(region_path),),
    ))
    assert item.material_id == "panel"
    assert item.assignment_id == "assignment.panel"


def test_catalog_and_exact_source_identifiers_are_preserved():
    item = accepted(analyze(materials(((125, 0.2),))))
    assert item.catalog_entry_id == "catalog:panel:v1"
    assert item.path_id == "path.front"
    assert item.correlation_id == "correlation.front"
    assert item.observed_event_id == "etc_event.left.144"
    assert {link.source_id for link in item.evidence_links} == {
        "path.front", "correlation.front", "panel"
    }


def test_material_confidence_is_conservative_across_profile_and_assignment():
    assert accepted(analyze(materials(((125, 0.2),)))).material_confidence == 76.0


def test_candidate_always_declares_no_causality_and_no_eligibility_impact():
    item = accepted(analyze(materials(((125, 0.2),))))
    assert item.causality_status is ReflectionCandidateCausalityStatus.NOT_ESTABLISHED
    assert item.eligibility_impact is ReflectionCandidateEligibilityImpact.NONE


def test_material_limitations_forbid_reflected_level_prediction():
    limitations = accepted(analyze(materials(((125, 0.2),)))).limitations
    assert "NO_REFLECTED_LEVEL_PREDICTION" in limitations
    assert "EVENT_FREQUENCY_RESPONSE_UNAVAILABLE" in limitations
    assert "INCIDENCE_AREA_DIRECTIVITY_AND_DIFFUSION_UNMODELED" in limitations


def test_missing_material_limitation_is_explicit():
    assert "MATERIAL_PROFILE_UNAVAILABLE" in accepted(analyze()).limitations


def test_ranking_is_deterministic_with_stable_identifier_tie_break():
    first = path("path.b", surface_id="right_wall", base="right_wall")
    second = path("path.a")
    result = analyze(
        paths=(first, second),
        correlations=(
            correlation(first, code="correlation.b", score=80),
            correlation(second, code="correlation.a", score=80),
        ),
    )
    ranks = {item.correlation_id: item.informative_rank for item in result.candidates}
    assert ranks == {"correlation.a": 1, "correlation.b": 2}


def test_ranking_orders_by_material_weakened_overall_score():
    first = path("path.a")
    second = path("path.b", surface_id="right_wall", base="right_wall")
    material = materials(((125, 0.8),))
    result = analyze(
        material,
        paths=(first, second),
        correlations=(
            correlation(first, code="correlation.a", score=100),
            correlation(second, code="correlation.b", score=70),
        ),
    )
    ranks = {item.correlation_id: item.informative_rank for item in result.candidates}
    assert ranks["correlation.b"] == 1
    assert ranks["correlation.a"] == 2


@pytest.mark.parametrize(
    ("score", "expected"),
    [(79.999, ReflectionCandidateStatus.CANDIDATE),
     (80.0, ReflectionCandidateStatus.STRONG_CANDIDATE),
     (100.0, ReflectionCandidateStatus.STRONG_CANDIDATE)],
)
def test_status_is_only_an_informative_score_label(score, expected):
    item_path = path()
    item = accepted(analyze(
        paths=(item_path,),
        correlations=(correlation(item_path, score=score),),
    ))
    assert item.status is expected
    assert item.eligibility_impact is ReflectionCandidateEligibilityImpact.NONE


def test_engine_does_not_mutate_any_source_object():
    geometry = GeometryEarlyReflectionAnalysis((path(),), ("G",), ("R",))
    correlations = ETCReflectionCorrelationAnalysis(
        correlations=[correlation(geometry.paths[0])]
    )
    material = materials(((125, 0.2),))
    snapshots = tuple(repr(item) for item in (geometry, correlations, material))
    ReflectionCandidateCompatibilityEngine().analyze(
        geometry, correlations, material
    )
    assert tuple(repr(item) for item in (geometry, correlations, material)) == snapshots


def test_same_inputs_produce_equal_analysis_objects():
    geometry = GeometryEarlyReflectionAnalysis((path(),), ("G",), ("R",))
    correlations = ETCReflectionCorrelationAnalysis(
        correlations=[correlation(geometry.paths[0])]
    )
    material = materials(((125, 0.2),))
    engine = ReflectionCandidateCompatibilityEngine()
    assert engine.analyze(geometry, correlations, material) == engine.analyze(
        geometry, correlations, material
    )


class StrictSourceView:
    """Fails on every undeclared dependency or service access."""

    def __init__(self, **allowed):
        object.__setattr__(self, "_allowed", allowed)

    def __getattr__(self, name):
        if name in self._allowed:
            return self._allowed[name]
        raise AssertionError(f"forbidden dependency accessed: {name}")


def test_engine_runs_with_only_three_minimal_synthetic_source_views():
    item_path = path()
    result = ReflectionCandidateCompatibilityEngine().analyze(
        StrictSourceView(paths=(item_path,)),
        StrictSourceView(correlations=[correlation(item_path)]),
        StrictSourceView(
            target_availability=materials(None).target_availability,
            assignments=(), materials=(),
        ),
    )
    assert len(result.candidates) == 1


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "room_description", "propagation_geometry", "material_catalog",
        "measurements", "impulse_response", "etc_detector", "path_generator",
        "temporal_correlation_engine", "planner", "protocol", "causal_decision",
    ],
)
def test_minimal_source_views_prove_forbidden_fields_are_not_accessed(forbidden_field):
    item_path = path()
    sources = (
        StrictSourceView(paths=(item_path,)),
        StrictSourceView(correlations=[correlation(item_path)]),
        StrictSourceView(
            target_availability=materials(None).target_availability,
            assignments=(), materials=(),
        ),
    )
    assert not any(forbidden_field in source._allowed for source in sources)
    assert ReflectionCandidateCompatibilityEngine().analyze(*sources).candidates


def valid_assessment(**changes):
    item = accepted(analyze())
    return replace(item, **changes)


def test_model_rejects_material_score_above_geometry():
    with pytest.raises(ValueError, match="cannot exceed"):
        valid_assessment(overall_compatibility_score=91.0)


def test_model_rejects_non_neutral_unknown_material_score():
    with pytest.raises(ValueError, match="score-neutral"):
        valid_assessment(overall_compatibility_score=89.0)


def test_model_rejects_rank_on_geometrically_rejected_path():
    rejected = analyze(correlations=()).candidates[0]
    with pytest.raises(ValueError, match="cannot receive"):
        replace(rejected, informative_rank=1)


def test_output_models_contain_no_decision_or_protocol_fields():
    names = {
        field.name
        for model in (ReflectionCandidateAssessment, MaterialAwareReflectionCandidateAnalysis)
        for field in fields(model)
    }
    assert names.isdisjoint({
        "hypothesis", "recommendation", "protocol", "decision",
        "eligible", "eligibility", "causal_conclusion",
    })


def test_stage_delegates_exactly_the_three_existing_analysis_objects():
    class RecordingEngine:
        def __init__(self):
            self.inputs = None
            self.result = MaterialAwareReflectionCandidateAnalysis((), (), ())

        def analyze(self, *inputs):
            self.inputs = inputs
            return self.result

    context = AnalysisContext(Measurement("stereo"))
    context.geometry_early_reflection_analysis = object()
    context.etc_reflection_correlation_analysis = object()
    context.surface_material_analysis = object()
    engine = RecordingEngine()
    MaterialAwareReflectionCandidateStage(engine).run(context)
    assert engine.inputs == (
        context.geometry_early_reflection_analysis,
        context.etc_reflection_correlation_analysis,
        context.surface_material_analysis,
    )
    assert context.material_aware_reflection_candidate_analysis is engine.result


def test_pipeline_places_leaf_stage_after_etc_correlation_and_before_reasoning():
    source = getsource(BrainPipeline.run)
    assert source.index("ETCCorrelationStage().run") < source.index(
        "MaterialAwareReflectionCandidateStage().run"
    ) < source.index("AcousticReasoningStage().run")


def test_core_snapshot_does_not_denormalize_timing_values():
    names = {field.name for field in fields(ReflectionCandidateAssessment)}
    assert names.isdisjoint({
        "theoretical_delay_ms", "measured_delay_ms", "timing_error_ms"
    })


def test_presenter_resolves_timing_only_through_correlation_id():
    item_path = path()
    source_correlation = correlation(item_path)
    context = AnalysisContext(Measurement("stereo"))
    context.etc_reflection_correlation_analysis = (
        ETCReflectionCorrelationAnalysis(correlations=[source_correlation])
    )
    context.material_aware_reflection_candidate_analysis = analyze(
        paths=(item_path,), correlations=(source_correlation,)
    )
    presented = MaterialAwareReflectionCandidatePresenter().present(context)
    candidate = presented.candidates[0]
    assert candidate.theoretical_delay_ms == source_correlation.theoretical_delay_ms
    assert candidate.measured_delay_ms == source_correlation.measured_delay_ms
    assert candidate.timing_error_ms == source_correlation.timing_error_ms


def test_report_builder_and_console_publish_descriptive_disclaimers(capsys):
    item_path = path()
    source_correlation = correlation(item_path)
    context = AnalysisContext(Measurement("stereo"))
    context.etc_reflection_correlation_analysis = (
        ETCReflectionCorrelationAnalysis(correlations=[source_correlation])
    )
    context.material_aware_reflection_candidate_analysis = analyze(
        paths=(item_path,), correlations=(source_correlation,)
    )
    report = ReportBuilder().build(SimpleNamespace(name="fixture"), context)
    ConsoleReporter().print(report)
    output = capsys.readouterr().out
    assert "Material-aware reflection candidates" in output
    assert "Causality: NOT_ESTABLISHED" in output
    assert "Eligibility impact: NONE" in output


def test_traceability_links_candidate_without_hypothesis_protocol_or_action():
    analysis = analyze(materials(((125, 0.2),)))
    evidence, links = TraceabilityEngine._material_candidate_graph(analysis)
    assert evidence[0].source_analysis == "MaterialAwareReflectionCandidateAnalysis"
    assert links[0].candidate_codes == (analysis.candidates[0].candidate_id,)
    assert links[0].hypothesis_codes == ()
    assert links[0].protocol_codes == ()
    assert links[0].action_codes == ()


def test_no_upstream_analysis_depends_on_pr035():
    root = Path(__file__).resolve().parents[1]
    for upstream_file in (
        "acousticbrain/analysis/geometry_early_reflection.py",
        "acousticbrain/analysis/etc_reflection_correlation.py",
        "acousticbrain/analysis/surface_material.py",
        "acousticbrain/analysis/acoustic_reasoning.py",
        "acousticbrain/analysis/experiment_planning.py",
    ):
        source = (root / upstream_file).read_text()
        assert "MaterialAwareReflectionCandidate" not in source
        assert "ReflectionCandidateCompatibilityEngine" not in source


def test_report_presentation_does_not_change_source_analysis_objects():
    item_path = path()
    source_correlation = correlation(item_path)
    context = AnalysisContext(Measurement("stereo"))
    context.etc_reflection_correlation_analysis = (
        ETCReflectionCorrelationAnalysis(correlations=[source_correlation])
    )
    context.material_aware_reflection_candidate_analysis = analyze(
        paths=(item_path,), correlations=(source_correlation,)
    )
    snapshot = repr(context.etc_reflection_correlation_analysis)
    MaterialAwareReflectionCandidatePresenter().present(context)
    assert repr(context.etc_reflection_correlation_analysis) == snapshot
