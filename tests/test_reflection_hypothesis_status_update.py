from dataclasses import fields, replace
from inspect import getsource, signature
from pathlib import Path
from types import SimpleNamespace

import pytest

from acousticbrain.analysis import (
    AnalysisContext,
    ControlledReflectionHypothesisStatusUpdateEngine,
    TraceabilityEngine,
)
from acousticbrain.application import (
    ControlledReflectionExperimentDeclarationService,
    ControlledReflectionHypothesisStatusUpdateService,
)
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.brain.pipeline import BrainPipeline
from acousticbrain.brain.stages.reflection_hypothesis_status_update import (
    ControlledReflectionHypothesisStatusUpdateStage,
)
from acousticbrain.models import (
    ControlledReflectionExperimentComparison,
    ControlledReflectionHypothesisStatusUpdate,
    ControlledReflectionHypothesisStatusUpdateRegistry,
    ControlledReflectionVerificationPlanningAnalysis,
    Measurement,
    ObservedReflectionDifference,
    ReflectionCandidateVerificationProposal,
    ReflectionComparisonCausalityStatus,
    ReflectionComparisonImpact,
    ReflectionExperimentComparisonStatus,
    ReflectionExperimentDeclarationStatus,
    ReflectionHypothesisImpact,
    ReflectionHypothesisObservationStatus,
    ReflectionVerificationCausalityStatus,
    ReflectionVerificationExecutionStatus,
    ReflectionVerificationImpact,
    ReflectionVerificationMethod,
)
from acousticbrain.persistence import (
    ControlledReflectionHypothesisStatusJsonCodec,
    ControlledReflectionHypothesisStatusJsonRepository,
)
from acousticbrain.report import ConsoleReporter


PROPOSAL_ID = "reflection_verification_proposal.candidate.front"
CANDIDATE_ID = "candidate.front"
DECLARATION_ID = f"reflection_experiment_declaration.{PROPOSAL_ID}"
COMPARISON_ID = f"reflection_experiment_comparison.{DECLARATION_ID}"
LEVEL = "etc.observed_event_relative_level_db"


def proposal():
    return ReflectionCandidateVerificationProposal(
        proposal_id=PROPOSAL_ID,
        source_candidate_id=CANDIDATE_ID,
        proposal_order=1,
        correlation_id="correlation.front",
        path_id="path.front",
        surface_id="front_wall",
        region_id=None,
        observed_event_id="etc_event.left.144",
        target_kind="SURFACE",
        target_id="front_wall",
        method=ReflectionVerificationMethod.TEMPORARY_MASK,
        reference_condition_code="UNMASKED_REFERENCE",
        intervention_condition_code="TEMPORARY_MASK_APPLIED",
        controlled_variable_codes=("MICROPHONE_POSITION",),
        changed_variable_codes=("TEMPORARY_MASK_STATE",),
        observable_fact_codes=(LEVEL,),
        supporting_outcome_codes=("REFLECTION_DECREASES_AFTER_MASKING",),
        counter_outcome_codes=("REFLECTION_REMAINS_UNCHANGED_AFTER_MASKING",),
        source_evidence_codes=("evidence.front",),
        source_provenance_codes=("PR035",),
        planning_rule_codes=("PR036",),
        execution_status=ReflectionVerificationExecutionStatus.NOT_EXECUTED,
        causality_status=ReflectionVerificationCausalityStatus.NOT_ESTABLISHED,
        eligibility_impact=ReflectionVerificationImpact.NONE,
        recommendation_impact=ReflectionVerificationImpact.NONE,
        limitations=("CAUSALITY_NOT_ESTABLISHED",),
    )


def declaration():
    planning = ControlledReflectionVerificationPlanningAnalysis(
        proposals=(proposal(),),
        exclusions=(),
        source_analysis_codes=("MaterialAwareReflectionCandidateAnalysis",),
        applied_rule_codes=("PR036",),
    )
    service = ControlledReflectionExperimentDeclarationService()
    baseline = service.measurement_reference(
        reference_id="baseline",
        experiment_id="exp-010",
        measurement_name="stereo",
        manifest_id="manifest.exp-010",
    )
    intervention = service.measurement_reference(
        reference_id="masked",
        experiment_id="exp-011",
        measurement_name="stereo",
        manifest_id="manifest.exp-011",
    )
    return service.declare(
        planning,
        proposal_id=PROPOSAL_ID,
        status=ReflectionExperimentDeclarationStatus.EXECUTED,
        declarer_id="operator.seb",
        reference_measurements=(baseline,),
        intervention_measurements=(intervention,),
    )


def difference(code=LEVEL, signed=-3.0):
    baseline = -8.0 if code == LEVEL else 3.0
    return ObservedReflectionDifference(
        observable_code=code,
        unit="dB" if code == LEVEL else "ms",
        baseline_value=baseline,
        intervention_value=baseline + signed,
        signed_difference=signed,
        absolute_difference=abs(signed),
        baseline_provenance_codes=("analysis.baseline",),
        intervention_provenance_codes=("analysis.intervention",),
    )


def comparison(status=ReflectionExperimentComparisonStatus.CHANGE_OBSERVED, *, signed=-3.0, differences=None):
    if differences is None:
        differences = (
            () if status in {
                ReflectionExperimentComparisonStatus.NOT_COMPARABLE,
                ReflectionExperimentComparisonStatus.INCONCLUSIVE,
            } else (difference(signed=signed),)
        )
    reasons = (
        ("NOT_COMPARABLE_FIXTURE",)
        if status is ReflectionExperimentComparisonStatus.NOT_COMPARABLE
        else (("INCONCLUSIVE_FIXTURE",) if status is ReflectionExperimentComparisonStatus.INCONCLUSIVE else ())
    )
    return ControlledReflectionExperimentComparison(
        comparison_id=COMPARISON_ID,
        experiment_declaration_id=DECLARATION_ID,
        proposal_id=PROPOSAL_ID,
        status=status,
        temporal_window_code="etc_event.left.144",
        baseline_measurement_reference_ids=("baseline",),
        intervention_measurement_reference_ids=("masked",),
        observed_differences=tuple(differences),
        reason_codes=reasons,
        causality_status=ReflectionComparisonCausalityStatus.NOT_ESTABLISHED,
        ranking_impact=ReflectionComparisonImpact.NONE,
        recommendation_impact=ReflectionComparisonImpact.NONE,
        eligibility_impact=ReflectionComparisonImpact.NONE,
        source_analysis_codes=("ControlledReflectionExperimentComparison",),
        applied_rule_codes=("PR038",),
    )


def update(item=None):
    return ControlledReflectionHypothesisStatusUpdateEngine().analyze(
        proposal(), declaration(), item if item is not None else comparison()
    )


def test_engine_signature_prevents_implicit_multi_experiment_aggregation():
    assert tuple(signature(
        ControlledReflectionHypothesisStatusUpdateEngine.analyze
    ).parameters) == ("self", "proposal", "declaration", "comparison")


def test_status_vocabulary_is_closed_and_prudent():
    assert tuple(item.value for item in ReflectionHypothesisObservationStatus) == (
        "UNCHANGED",
        "INCONCLUSIVE",
        "SUPPORTED_BY_OBSERVATION",
        "NOT_SUPPORTED_BY_OBSERVATION",
        "NOT_ASSESSABLE",
    )


@pytest.mark.parametrize(
    ("comparison_status", "expected"),
    [
        (
            ReflectionExperimentComparisonStatus.NOT_COMPARABLE,
            ReflectionHypothesisObservationStatus.NOT_ASSESSABLE,
        ),
        (
            ReflectionExperimentComparisonStatus.INCONCLUSIVE,
            ReflectionHypothesisObservationStatus.INCONCLUSIVE,
        ),
        (
            ReflectionExperimentComparisonStatus.NO_OBSERVABLE_CHANGE,
            ReflectionHypothesisObservationStatus.NOT_SUPPORTED_BY_OBSERVATION,
        ),
    ],
)
def test_direct_pr038_status_transitions_are_deterministic(comparison_status, expected):
    result = update(comparison(comparison_status, signed=0.0))
    assert result.status is expected
    assert len(result.transition_rule_codes) == 5


def test_target_level_decrease_supports_only_observation_status():
    result = update(comparison(signed=-3.25))
    assert result.status is ReflectionHypothesisObservationStatus.SUPPORTED_BY_OBSERVATION
    assert result.target_kind == "CANDIDATE"
    assert result.target_id == CANDIDATE_ID
    assert result.causality_status.value == "NOT_ESTABLISHED"
    assert result.recommendation_impact is ReflectionHypothesisImpact.NONE
    assert result.ranking_impact is ReflectionHypothesisImpact.NONE
    assert result.eligibility_impact is ReflectionHypothesisImpact.NONE


def test_target_level_increase_is_not_supported_within_observed_protocol():
    result = update(comparison(signed=2.0))
    assert result.status is ReflectionHypothesisObservationStatus.NOT_SUPPORTED_BY_OBSERVATION
    assert result.justification_codes == (
        "TARGET_EVENT_LEVEL_DID_NOT_DECREASE_AFTER_INTERVENTION",
    )


def test_change_without_target_level_difference_remains_inconclusive():
    result = update(comparison(differences=(
        difference("etc.observed_event_delay_ms", signed=0.5),
    )))
    assert result.status is ReflectionHypothesisObservationStatus.INCONCLUSIVE
    assert result.justification_codes == ("TARGET_LEVEL_DECREASE_NOT_OBSERVED",)


def test_absent_comparison_is_explicitly_not_assessable():
    result = ControlledReflectionHypothesisStatusUpdateEngine().analyze(
        proposal(), declaration(), None
    )
    assert result.status is ReflectionHypothesisObservationStatus.NOT_ASSESSABLE
    assert result.comparison_id is None
    assert result.measured_fact_codes == ()
    assert result.comparison_result_codes == ()
    assert result.justification_codes == ("COMPARISON_ABSENT",)


def test_incoherent_links_are_not_assessable_instead_of_reinterpreted():
    result = ControlledReflectionHypothesisStatusUpdateEngine().analyze(
        proposal(), declaration(), replace(comparison(), proposal_id="other")
    )
    assert result.status is ReflectionHypothesisObservationStatus.NOT_ASSESSABLE
    assert result.justification_codes == ("COMPARISON_LINK_INCOHERENT",)


def test_provenance_categories_are_strictly_separated():
    result = update()
    categories = (
        set(result.measured_fact_codes),
        set(result.comparison_result_codes),
        set(result.transition_rule_codes),
        set(result.status_provenance_codes),
        set(result.justification_codes),
    )
    for index, first in enumerate(categories):
        for second in categories[index + 1:]:
            assert first.isdisjoint(second)


def test_same_inputs_produce_identical_output_and_do_not_mutate_sources():
    source_proposal = proposal()
    source_declaration = declaration()
    source_comparison = comparison()
    before = tuple(map(repr, (source_proposal, source_declaration, source_comparison)))
    engine = ControlledReflectionHypothesisStatusUpdateEngine()
    assert engine.analyze(source_proposal, source_declaration, source_comparison) == (
        engine.analyze(source_proposal, source_declaration, source_comparison)
    )
    assert before == tuple(map(repr, (source_proposal, source_declaration, source_comparison)))


def test_model_has_no_surface_attribution_score_recommendation_or_eligibility_decision():
    names = {field.name for field in fields(ControlledReflectionHypothesisStatusUpdate)}
    assert names.isdisjoint({
        "surface_id", "confirmed_surface_id", "causal_conclusion",
        "score", "rank", "recommendation", "eligible",
    })


def test_model_rejects_causal_target_kind_and_non_none_impacts():
    result = update()
    with pytest.raises(ValueError, match="candidates only"):
        replace(result, target_kind="SURFACE")
    with pytest.raises(ValueError, match="cannot affect decisions"):
        replace(result, recommendation_impact=object())


def test_json_round_trip_is_deterministic():
    registry = ControlledReflectionHypothesisStatusUpdateRegistry((update(),))
    codec = ControlledReflectionHypothesisStatusJsonCodec()
    payload = codec.dumps(registry)
    assert codec.loads(payload) == registry
    assert codec.dumps(codec.loads(payload)) == payload


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "[]",
        '{"schema_version": 2, "updates": []}',
        '{"schema_version": 1, "updates": {}}',
    ],
)
def test_json_rejects_invalid_or_unknown_payloads(payload):
    with pytest.raises(ValueError):
        ControlledReflectionHypothesisStatusJsonCodec().loads(payload)


def test_repository_is_atomic_idempotent_and_missing_is_empty(tmp_path):
    path = tmp_path / "reflection-hypothesis-status.json"
    repository = ControlledReflectionHypothesisStatusJsonRepository()
    assert repository.load(path).updates == ()
    registry = ControlledReflectionHypothesisStatusUpdateRegistry((update(),))
    assert repository.save(path, registry) is True
    assert repository.save(path, registry) is False
    assert repository.load(path) == registry
    assert not path.with_suffix(".json.tmp").exists()


def test_service_loads_updates_explicitly_into_project(tmp_path):
    path = tmp_path / "reflection-hypothesis-status.json"
    service = ControlledReflectionHypothesisStatusUpdateService()
    service.save(path, (update(),))
    project = SimpleNamespace(controlled_reflection_hypothesis_status_updates=())
    registry = service.load_into_project(project, path)
    assert project.controlled_reflection_hypothesis_status_updates == registry.updates


def test_stage_publishes_persisted_updates_without_reasoning_mutation():
    item = update()
    project = SimpleNamespace(controlled_reflection_hypothesis_status_updates=(item,))
    context = AnalysisContext(Measurement("stereo"))
    context.acoustic_reasoning_analysis = object()
    before = context.acoustic_reasoning_analysis
    ControlledReflectionHypothesisStatusUpdateStage().run(project, context)
    assert context.controlled_reflection_hypothesis_status_updates == (item,)
    assert context.acoustic_reasoning_analysis is before


def test_pipeline_places_status_update_after_comparison_and_before_reasoning():
    source = getsource(BrainPipeline.run)
    assert source.index("ControlledReflectionExperimentComparisonStage().run") < (
        source.index("ControlledReflectionHypothesisStatusUpdateStage().run")
    ) < source.index("AcousticReasoningStage().run")


def test_report_presents_status_provenance_and_all_limits(capsys):
    context = AnalysisContext(Measurement("stereo"))
    context.controlled_reflection_hypothesis_status_updates = (update(),)
    report = ReportBuilder().build(SimpleNamespace(name="fixture"), context)
    ConsoleReporter().print(report)
    output = capsys.readouterr().out
    assert "Controlled reflection hypothesis observation status" in output
    assert "Observation status: SUPPORTED_BY_OBSERVATION" in output
    assert "Measured facts:" in output
    assert "Transition rules:" in output
    assert "Status provenance:" in output
    assert "Causality: NOT_ESTABLISHED" in output
    assert "Recommendation impact: NONE" in output
    assert "Ranking impact: NONE" in output
    assert "Eligibility impact: NONE" in output


def test_traceability_preserves_full_chain_without_causal_or_decision_links():
    item = update()
    link = TraceabilityEngine._reflection_hypothesis_status_update_graph((item,))[0]
    assert link.candidate_codes == (CANDIDATE_ID,)
    assert link.verification_proposal_codes == (PROPOSAL_ID,)
    assert link.experiment_declaration_codes == (DECLARATION_ID,)
    assert link.experiment_comparison_codes == (COMPARISON_ID,)
    assert link.hypothesis_status_update_codes == (item.update_id,)
    assert link.hypothesis_codes == ()
    assert link.recommendation_codes == ()
    assert link.ranking_codes == ()
    assert link.recommended_candidate_codes == ()


def test_engine_has_no_llm_hidden_repository_or_upstream_decision_access():
    source = getsource(ControlledReflectionHypothesisStatusUpdateEngine).lower()
    for forbidden in (
        "openai", "ollama", "get_measurement", "impulseresponse",
        "repository", "acousticreasoning", "recommendationengine",
    ):
        assert forbidden not in source
    root = Path(__file__).resolve().parents[1]
    for relative in (
        "acousticbrain/analysis/acoustic_reasoning.py",
        "acousticbrain/analysis/experiment_planning.py",
        "acousticbrain/analysis/recommendation.py",
        "acousticbrain/analysis/reflection_verification_planning.py",
        "acousticbrain/analysis/reflection_experiment_comparison.py",
    ):
        assert "ControlledReflectionHypothesisStatusUpdate" not in (
            root / relative
        ).read_text()
