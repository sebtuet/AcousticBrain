from dataclasses import fields, replace
from inspect import getsource, signature
from pathlib import Path
from types import SimpleNamespace

import pytest

from acousticbrain.analysis import (
    AnalysisContext,
    ControlledReflectionVerificationPlanningEngine,
    TraceabilityEngine,
)
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.brain.pipeline import BrainPipeline
from acousticbrain.brain.stages.reflection_verification_planning import (
    ControlledReflectionVerificationPlanningStage,
)
from acousticbrain.models import (
    ControlledReflectionVerificationPlanningAnalysis,
    MaterialAssessment,
    MaterialAwareReflectionCandidateAnalysis,
    Measurement,
    ReflectionCandidateAssessment,
    ReflectionCandidateCausalityStatus,
    ReflectionCandidateEligibilityImpact,
    ReflectionCandidateEvidenceLink,
    ReflectionCandidateGeometricStatus,
    ReflectionCandidateStatus,
    ReflectionCandidateVerificationProposal,
    ReflectionVerificationCausalityStatus,
    ReflectionVerificationExecutionStatus,
    ReflectionVerificationImpact,
)
from acousticbrain.report import (
    ConsoleReporter,
    ControlledReflectionVerificationPlanningPresenter,
)


def candidate(
    candidate_id="material_reflection_candidate.correlation.front",
    *,
    rank=1,
    rejected=False,
    region_id=None,
):
    correlation_id = None if rejected else f"correlation.{candidate_id.rsplit('.', 1)[-1]}"
    return ReflectionCandidateAssessment(
        candidate_id=candidate_id,
        correlation_id=correlation_id,
        path_id=f"path.{candidate_id.rsplit('.', 1)[-1]}",
        surface_id="front_wall",
        region_id=region_id,
        observed_event_id=None if rejected else "etc_event.left.144",
        geometric_temporal_score=0.0 if rejected else 90.0,
        geometric_confidence=88.0,
        geometric_status=(
            ReflectionCandidateGeometricStatus.REJECTED
            if rejected
            else ReflectionCandidateGeometricStatus.ACCEPTED
        ),
        material_assessment=MaterialAssessment.UNKNOWN,
        material_confidence=None,
        material_id=None,
        assignment_id=None,
        catalog_entry_id=None,
        overall_compatibility_score=0.0 if rejected else 90.0,
        informative_rank=None if rejected else rank,
        status=(
            ReflectionCandidateStatus.REJECTED
            if rejected
            else ReflectionCandidateStatus.STRONG_CANDIDATE
        ),
        causality_status=ReflectionCandidateCausalityStatus.NOT_ESTABLISHED,
        eligibility_impact=ReflectionCandidateEligibilityImpact.NONE,
        evidence_links=(ReflectionCandidateEvidenceLink(
            code=f"evidence.{candidate_id}.geometry",
            source_analysis="GeometryEarlyReflectionAnalysis",
            source_id=f"path.{candidate_id.rsplit('.', 1)[-1]}",
            fact_code="GEOMETRIC_TEMPORAL_COMPATIBILITY",
        ),),
        limitations=("CAUSALITY_NOT_ESTABLISHED",),
        provenance_codes=("GEOMETRY-SOURCE", "CORRELATION-SOURCE"),
        rules_applied=("GEOMETRY_TEMPORAL_SCORE_DOMINATES",),
    )


def analysis(*items):
    return MaterialAwareReflectionCandidateAnalysis(
        candidates=tuple(items or (candidate(),)),
        source_analysis_codes=(
            "GeometryEarlyReflectionAnalysis",
            "ETCReflectionCorrelationAnalysis",
            "SurfaceMaterialAnalysis",
        ),
        applied_rule_codes=("GEOMETRY_TEMPORAL_SCORE_DOMINATES",),
    )


def plan(*items):
    return ControlledReflectionVerificationPlanningEngine().analyze(
        analysis(*items)
    )


def test_engine_signature_contains_exactly_one_source_analysis():
    assert tuple(signature(
        ControlledReflectionVerificationPlanningEngine.analyze
    ).parameters) == ("self", "candidate_analysis")


def test_analysis_declares_only_pr035_as_its_source():
    assert plan().source_analysis_codes == (
        "MaterialAwareReflectionCandidateAnalysis",
    )


def test_accepted_candidate_produces_descriptive_unexecuted_proposal():
    proposal = plan().proposals[0]
    assert proposal.proposal_id == (
        "reflection_verification_proposal."
        "material_reflection_candidate.correlation.front"
    )
    assert proposal.execution_status is ReflectionVerificationExecutionStatus.NOT_EXECUTED
    assert proposal.causality_status is ReflectionVerificationCausalityStatus.NOT_ESTABLISHED
    assert proposal.eligibility_impact is ReflectionVerificationImpact.NONE
    assert proposal.recommendation_impact is ReflectionVerificationImpact.NONE


def test_order_is_inherited_without_reranking_and_input_order_is_irrelevant():
    first = candidate("material_reflection_candidate.correlation.first", rank=1)
    second = candidate("material_reflection_candidate.correlation.second", rank=2)
    forward = plan(first, second)
    reverse = plan(second, first)
    assert forward == reverse
    assert tuple(item.source_candidate_id for item in forward.proposals) == (
        first.candidate_id,
        second.candidate_id,
    )
    assert tuple(item.proposal_order for item in forward.proposals) == (1, 2)


def test_rejected_candidate_remains_excluded_and_never_becomes_a_proposal():
    rejected = candidate(
        "material_reflection_candidate.rejected.path.side", rejected=True
    )
    result = plan(rejected)
    assert result.proposals == ()
    assert result.exclusions[0].source_candidate_id == rejected.candidate_id
    assert result.exclusions[0].reason.value == "GEOMETRICALLY_REJECTED"


def test_region_target_is_preserved_without_reopening_geometry():
    proposal = plan(candidate(region_id="front_wall.panel_zone")).proposals[0]
    assert proposal.target_kind == "REGION"
    assert proposal.target_id == "front_wall.panel_zone"
    assert proposal.surface_id == "front_wall"


def test_controlled_and_changed_variables_are_explicit_and_disjoint():
    proposal = plan().proposals[0]
    assert proposal.changed_variable_codes == ("TEMPORARY_MASK_STATE",)
    assert set(proposal.controlled_variable_codes).isdisjoint(
        proposal.changed_variable_codes
    )
    assert "MICROPHONE_POSITION" in proposal.controlled_variable_codes
    assert "MEASUREMENT_LEVEL" in proposal.controlled_variable_codes


def test_conditions_and_competing_outcomes_do_not_claim_an_observation():
    proposal = plan().proposals[0]
    assert proposal.reference_condition_code == "UNMASKED_REFERENCE"
    assert proposal.intervention_condition_code == "TEMPORARY_MASK_APPLIED"
    assert proposal.supporting_outcome_codes == (
        "REFLECTION_DECREASES_AFTER_MASKING",
    )
    assert proposal.counter_outcome_codes == (
        "REFLECTION_REMAINS_UNCHANGED_AFTER_MASKING",
    )
    assert proposal.execution_status.value == "NOT_EXECUTED"


def test_source_provenance_and_planning_rules_remain_separate():
    proposal = plan().proposals[0]
    assert proposal.source_provenance_codes == (
        "GEOMETRY-SOURCE", "CORRELATION-SOURCE"
    )
    assert set(proposal.source_provenance_codes).isdisjoint(
        proposal.planning_rule_codes
    )
    assert proposal.source_evidence_codes[0].endswith(
        ".overall_compatibility"
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("execution_status", object(), "cannot execute"),
        ("causality_status", object(), "cannot establish"),
        ("eligibility_impact", object(), "cannot affect eligibility"),
        ("recommendation_impact", object(), "cannot affect recommendations"),
    ],
)
def test_model_rejects_forbidden_state_transitions(field, value, message):
    with pytest.raises(ValueError, match=message):
        replace(plan().proposals[0], **{field: value})


def test_model_rejects_overlap_between_controlled_and_changed_variables():
    proposal = plan().proposals[0]
    with pytest.raises(ValueError, match="remain separate"):
        replace(
            proposal,
            changed_variable_codes=(proposal.controlled_variable_codes[0],),
        )


def test_models_contain_no_score_priority_protocol_or_execution_result_fields():
    names = {
        field.name
        for model in (
            ReflectionCandidateVerificationProposal,
            ControlledReflectionVerificationPlanningAnalysis,
        )
        for field in fields(model)
    }
    assert names.isdisjoint({
        "score", "priority", "protocol_id", "eligible", "recommended",
        "result", "causal_conclusion",
    })


def test_stage_delegates_exactly_the_existing_candidate_analysis():
    class RecordingEngine:
        def __init__(self):
            self.input = None
            self.result = ControlledReflectionVerificationPlanningAnalysis(
                (), (), (), ()
            )

        def analyze(self, value):
            self.input = value
            return self.result

    context = AnalysisContext(Measurement("stereo"))
    context.material_aware_reflection_candidate_analysis = object()
    engine = RecordingEngine()
    ControlledReflectionVerificationPlanningStage(engine).run(context)
    assert engine.input is context.material_aware_reflection_candidate_analysis
    assert context.controlled_reflection_verification_planning_analysis is engine.result


def test_pipeline_places_leaf_after_pr035_and_before_reasoning():
    source = getsource(BrainPipeline.run)
    assert source.index("MaterialAwareReflectionCandidateStage().run") < source.index(
        "ControlledReflectionVerificationPlanningStage().run"
    ) < source.index("AcousticReasoningStage().run")


def test_engine_does_not_mutate_source_analysis():
    source = analysis(candidate())
    snapshot = repr(source)
    ControlledReflectionVerificationPlanningEngine().analyze(source)
    assert repr(source) == snapshot


def test_engine_contains_no_llm_or_hidden_source_access():
    source = getsource(ControlledReflectionVerificationPlanningEngine).lower()
    assert "ollama" not in source
    assert "openai" not in source
    assert "roomdescription" not in source
    assert "get_measurement" not in source
    assert "from acousticbrain.project" not in source
    assert "experimentplanner" not in source


def test_stage_does_not_mutate_reasoning_planning_or_recommendations():
    context = AnalysisContext(Measurement("stereo"))
    context.material_aware_reflection_candidate_analysis = analysis(candidate())
    context.acoustic_reasoning_analysis = object()
    context.experiment_planning_analysis = object()
    context.recommendation_analysis = object()
    before = (
        context.acoustic_reasoning_analysis,
        context.experiment_planning_analysis,
        context.recommendation_analysis,
    )
    ControlledReflectionVerificationPlanningStage().run(context)
    assert before == (
        context.acoustic_reasoning_analysis,
        context.experiment_planning_analysis,
        context.recommendation_analysis,
    )


def test_presenter_and_console_publish_all_scientific_disclaimers(capsys):
    context = AnalysisContext(Measurement("stereo"))
    context.controlled_reflection_verification_planning_analysis = plan()
    report = ReportBuilder().build(SimpleNamespace(name="fixture"), context)
    ConsoleReporter().print(report)
    output = capsys.readouterr().out
    assert "Controlled reflection verification proposals" in output
    assert "Execution: NOT_EXECUTED" in output
    assert "Causality: NOT_ESTABLISHED" in output
    assert "Eligibility impact: NONE" in output
    assert "Recommendation impact: NONE" in output


def test_presenter_omits_empty_analysis():
    context = AnalysisContext(Measurement("stereo"))
    context.controlled_reflection_verification_planning_analysis = (
        ControlledReflectionVerificationPlanningAnalysis((), (), (), ())
    )
    assert ControlledReflectionVerificationPlanningPresenter().present(context) is None


def test_traceability_links_proposal_without_decision_or_protocol_links():
    result = plan()
    links = TraceabilityEngine._reflection_verification_planning_graph(result)
    link = links[0]
    proposal = result.proposals[0]
    assert link.verification_proposal_codes == (proposal.proposal_id,)
    assert link.candidate_codes == (proposal.source_candidate_id,)
    assert link.evidence_codes == proposal.source_evidence_codes
    assert set(proposal.observable_fact_codes).isdisjoint(link.fact_codes)
    assert link.hypothesis_codes == ()
    assert link.protocol_codes == ()
    assert link.action_codes == ()
    assert link.recommendation_codes == ()
    assert link.recommended_candidate_codes == ()


def test_traceability_preserves_explicit_rejection_disposition():
    rejected = candidate(
        "material_reflection_candidate.rejected.path.side", rejected=True
    )
    links = TraceabilityEngine._reflection_verification_planning_graph(plan(rejected))
    assert links[0].candidate_codes == (rejected.candidate_id,)
    assert links[0].verification_proposal_codes == ()


def test_no_upstream_decision_analysis_depends_on_pr036():
    root = Path(__file__).resolve().parents[1]
    for upstream_file in (
        "acousticbrain/analysis/acoustic_reasoning.py",
        "acousticbrain/analysis/experiment_planning.py",
        "acousticbrain/analysis/recommendation.py",
    ):
        source = (root / upstream_file).read_text()
        assert "ControlledReflectionVerification" not in source
        assert "ReflectionCandidateVerificationProposal" not in source
