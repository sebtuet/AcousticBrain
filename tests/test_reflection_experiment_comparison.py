from dataclasses import fields, replace
from inspect import getsource, signature
from pathlib import Path
from types import SimpleNamespace

import pytest

from acousticbrain.analysis import (
    AnalysisContext,
    DeterministicReflectionExperimentComparisonEngine,
    TraceabilityEngine,
)
from acousticbrain.application import (
    ControlledReflectionExperimentComparisonService,
    ControlledReflectionExperimentDeclarationService,
)
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.brain.pipeline import BrainPipeline
from acousticbrain.brain.stages.reflection_experiment_comparison import (
    ControlledReflectionExperimentComparisonStage,
)
from acousticbrain.models import (
    ControlledReflectionExperimentComparison,
    ControlledReflectionExperimentComparisonRegistry,
    ControlledReflectionVerificationPlanningAnalysis,
    Measurement,
    ReflectionCandidateVerificationProposal,
    ReflectionComparisonImpact,
    ReflectionComparisonObservation,
    ReflectionExperimentComparisonStatus,
    ReflectionExperimentDeclarationStatus,
    ReflectionVerificationCausalityStatus,
    ReflectionVerificationExecutionStatus,
    ReflectionVerificationImpact,
    ReflectionVerificationMethod,
)
from acousticbrain.persistence import (
    ControlledReflectionExperimentComparisonJsonCodec,
    ControlledReflectionExperimentComparisonJsonRepository,
)
from acousticbrain.report import ConsoleReporter


PROPOSAL_ID = "reflection_verification_proposal.candidate.front"
WINDOW = "etc_event.left.144"
OBSERVABLES = (
    "etc.observed_event_delay_ms",
    "etc.observed_event_relative_level_db",
    "etc_reflection.geometry_timing_error_ms",
)
UNITS = {
    OBSERVABLES[0]: "ms",
    OBSERVABLES[1]: "dB",
    OBSERVABLES[2]: "ms",
}


def proposal():
    return ReflectionCandidateVerificationProposal(
        proposal_id=PROPOSAL_ID,
        source_candidate_id="candidate.front",
        proposal_order=1,
        correlation_id="correlation.front",
        path_id="path.front",
        surface_id="front_wall",
        region_id=None,
        observed_event_id=WINDOW,
        target_kind="SURFACE",
        target_id="front_wall",
        method=ReflectionVerificationMethod.TEMPORARY_MASK,
        reference_condition_code="UNMASKED_REFERENCE",
        intervention_condition_code="TEMPORARY_MASK_APPLIED",
        controlled_variable_codes=("MICROPHONE_POSITION",),
        changed_variable_codes=("TEMPORARY_MASK_STATE",),
        observable_fact_codes=OBSERVABLES,
        supporting_outcome_codes=("REFLECTION_DECREASES_AFTER_MASKING",),
        counter_outcome_codes=("REFLECTION_REMAINS_UNCHANGED_AFTER_MASKING",),
        source_evidence_codes=("evidence.candidate.front",),
        source_provenance_codes=("PR035",),
        planning_rule_codes=("PR036",),
        execution_status=ReflectionVerificationExecutionStatus.NOT_EXECUTED,
        causality_status=ReflectionVerificationCausalityStatus.NOT_ESTABLISHED,
        eligibility_impact=ReflectionVerificationImpact.NONE,
        recommendation_impact=ReflectionVerificationImpact.NONE,
        limitations=("CAUSALITY_NOT_ESTABLISHED",),
    )


def planning():
    return ControlledReflectionVerificationPlanningAnalysis(
        proposals=(proposal(),),
        exclusions=(),
        source_analysis_codes=("MaterialAwareReflectionCandidateAnalysis",),
        applied_rule_codes=("PR036",),
    )


def reference(reference_id, experiment_id):
    return ControlledReflectionExperimentDeclarationService.measurement_reference(
        reference_id=reference_id,
        experiment_id=experiment_id,
        measurement_name="stereo",
        manifest_id=f"manifest.{experiment_id}",
        content_hash=f"sha256:{reference_id}",
    )


def declaration(status=ReflectionExperimentDeclarationStatus.EXECUTED):
    executed = status is ReflectionExperimentDeclarationStatus.EXECUTED
    return ControlledReflectionExperimentDeclarationService().declare(
        planning(),
        proposal_id=PROPOSAL_ID,
        status=status,
        declarer_id="operator.seb",
        reference_measurements=(reference("baseline", "exp-010"),) if executed else (),
        intervention_measurements=(reference("masked", "exp-011"),) if executed else (),
    )


def observations(reference_id, values=None, codes=OBSERVABLES):
    values = values or {
        OBSERVABLES[0]: 3.0,
        OBSERVABLES[1]: -8.0,
        OBSERVABLES[2]: 0.1,
    }
    return tuple(
        ReflectionComparisonObservation(
            measurement_reference_id=reference_id,
            temporal_window_code=WINDOW,
            observable_code=code,
            value=values[code],
            unit=UNITS[code],
            provenance_codes=(f"analysis.{reference_id}.{code}",),
        )
        for code in codes
    )


def comparison(after=None):
    return DeterministicReflectionExperimentComparisonEngine().analyze(
        proposal(),
        declaration(),
        observations("baseline"),
        observations("masked", after),
    )


def test_engine_signature_has_only_explicit_scientific_inputs():
    assert tuple(signature(
        DeterministicReflectionExperimentComparisonEngine.analyze
    ).parameters) == (
        "self", "proposal", "declaration",
        "baseline_observations", "intervention_observations",
    )


def test_comparison_status_vocabulary_is_closed():
    assert tuple(item.value for item in ReflectionExperimentComparisonStatus) == (
        "NOT_COMPARABLE",
        "NO_OBSERVABLE_CHANGE",
        "CHANGE_OBSERVED",
        "INCONCLUSIVE",
    )


def test_equal_observations_are_described_as_no_observable_change():
    result = comparison()
    assert result.status is ReflectionExperimentComparisonStatus.NO_OBSERVABLE_CHANGE
    assert all(item.absolute_difference == 0.0 for item in result.observed_differences)
    assert result.temporal_window_code == WINDOW


def test_nonzero_arithmetic_difference_is_observed_without_causal_claim():
    values = {
        OBSERVABLES[0]: 3.0,
        OBSERVABLES[1]: -11.25,
        OBSERVABLES[2]: 0.1,
    }
    result = comparison(values)
    assert result.status is ReflectionExperimentComparisonStatus.CHANGE_OBSERVED
    level = next(
        item for item in result.observed_differences
        if item.observable_code == OBSERVABLES[1]
    )
    assert level.signed_difference == -3.25
    assert level.absolute_difference == 3.25
    assert result.causality_status.value == "NOT_ESTABLISHED"
    assert result.ranking_impact is ReflectionComparisonImpact.NONE
    assert result.recommendation_impact is ReflectionComparisonImpact.NONE
    assert result.eligibility_impact is ReflectionComparisonImpact.NONE


def test_partial_observable_coverage_is_inconclusive_but_preserves_differences():
    engine = DeterministicReflectionExperimentComparisonEngine()
    result = engine.analyze(
        proposal(), declaration(),
        observations("baseline"),
        observations("masked", codes=OBSERVABLES[:2]),
    )
    assert result.status is ReflectionExperimentComparisonStatus.INCONCLUSIVE
    assert result.reason_codes == ("OBSERVABLE_COVERAGE_INCOMPLETE",)
    assert len(result.observed_differences) == 2


@pytest.mark.parametrize(
    ("baseline", "intervention", "reason"),
    [
        ((), (), "OBSERVATIONS_MISSING"),
        (
            observations("wrong"), observations("masked"),
            "BASELINE_MEASUREMENT_REFERENCE_MISMATCH",
        ),
        (
            tuple(replace(item, temporal_window_code="other") for item in observations("baseline")),
            observations("masked"), "BASELINE_TEMPORAL_WINDOW_MISMATCH",
        ),
    ],
)
def test_non_comparable_inputs_are_explained_without_comparison(baseline, intervention, reason):
    result = DeterministicReflectionExperimentComparisonEngine().analyze(
        proposal(), declaration(), baseline, intervention
    )
    assert result.status is ReflectionExperimentComparisonStatus.NOT_COMPARABLE
    assert reason in result.reason_codes
    assert result.observed_differences == ()


def test_non_executed_declaration_is_not_comparable():
    result = DeterministicReflectionExperimentComparisonEngine().analyze(
        proposal(), declaration(ReflectionExperimentDeclarationStatus.PLANNED), (), ()
    )
    assert result.status is ReflectionExperimentComparisonStatus.NOT_COMPARABLE
    assert "DECLARATION_NOT_EXECUTED" in result.reason_codes


def test_proposal_declaration_mismatch_is_rejected():
    with pytest.raises(ValueError, match="must match"):
        DeterministicReflectionExperimentComparisonEngine().analyze(
            replace(proposal(), proposal_id="other"),
            declaration(), (), (),
        )


def test_observable_provenance_remains_separate_by_condition():
    result = comparison()
    difference = result.observed_differences[0]
    assert difference.baseline_provenance_codes != (
        difference.intervention_provenance_codes
    )
    assert difference.baseline_provenance_codes[0].startswith("analysis.baseline")
    assert difference.intervention_provenance_codes[0].startswith("analysis.masked")


def test_model_contains_no_hypothesis_surface_attribution_or_decision_fields():
    names = {field.name for field in fields(ControlledReflectionExperimentComparison)}
    assert names.isdisjoint({
        "hypothesis_status", "hypothesis_code", "confirmed_surface_id",
        "causal_conclusion", "score", "rank", "recommendation", "eligible",
    })


def test_model_rejects_change_status_without_a_numerical_change():
    with pytest.raises(ValueError, match="requires an observed numerical difference"):
        replace(
            comparison(),
            status=ReflectionExperimentComparisonStatus.CHANGE_OBSERVED,
        )


def test_non_comparable_and_inconclusive_statuses_require_reasons():
    with pytest.raises(ValueError, match="reasons are inconsistent"):
        replace(
            comparison(),
            status=ReflectionExperimentComparisonStatus.INCONCLUSIVE,
        )


def test_input_objects_are_not_mutated():
    source_proposal = proposal()
    source_declaration = declaration()
    baseline = observations("baseline")
    intervention = observations("masked")
    before = tuple(map(repr, (source_proposal, source_declaration, baseline, intervention)))
    DeterministicReflectionExperimentComparisonEngine().analyze(
        source_proposal, source_declaration, baseline, intervention
    )
    assert before == tuple(map(repr, (source_proposal, source_declaration, baseline, intervention)))


def test_json_round_trip_is_deterministic():
    registry = ControlledReflectionExperimentComparisonRegistry((comparison(),))
    codec = ControlledReflectionExperimentComparisonJsonCodec()
    payload = codec.dumps(registry)
    assert codec.loads(payload) == registry
    assert codec.dumps(codec.loads(payload)) == payload


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "[]",
        '{"schema_version": 2, "comparisons": []}',
        '{"schema_version": 1, "comparisons": {}}',
    ],
)
def test_json_rejects_invalid_or_unknown_payloads(payload):
    with pytest.raises(ValueError):
        ControlledReflectionExperimentComparisonJsonCodec().loads(payload)


def test_repository_is_atomic_idempotent_and_missing_is_empty(tmp_path):
    path = tmp_path / "reflection-comparisons.json"
    repository = ControlledReflectionExperimentComparisonJsonRepository()
    assert repository.load(path).comparisons == ()
    registry = ControlledReflectionExperimentComparisonRegistry((comparison(),))
    assert repository.save(path, registry) is True
    assert repository.save(path, registry) is False
    assert repository.load(path) == registry
    assert not path.with_suffix(".json.tmp").exists()


def test_service_loads_comparisons_explicitly_into_project(tmp_path):
    path = tmp_path / "reflection-comparisons.json"
    service = ControlledReflectionExperimentComparisonService()
    service.save(path, (comparison(),))
    project = SimpleNamespace(controlled_reflection_experiment_comparisons=())
    registry = service.load_into_project(project, path)
    assert project.controlled_reflection_experiment_comparisons == registry.comparisons


def test_stage_only_publishes_persisted_comparisons_in_stable_order():
    item = comparison()
    project = SimpleNamespace(controlled_reflection_experiment_comparisons=(item,))
    context = AnalysisContext(Measurement("stereo"))
    ControlledReflectionExperimentComparisonStage().run(project, context)
    assert context.controlled_reflection_experiment_comparisons == (item,)


def test_pipeline_places_comparison_after_declaration_and_before_reasoning():
    source = getsource(BrainPipeline.run)
    assert source.index("ControlledReflectionExperimentDeclarationStage().run") < (
        source.index("ControlledReflectionExperimentComparisonStage().run")
    ) < source.index("AcousticReasoningStage().run")


def test_report_presents_differences_and_all_scientific_limits(capsys):
    context = AnalysisContext(Measurement("stereo"))
    context.controlled_reflection_experiment_comparisons = (comparison({
        OBSERVABLES[0]: 3.0,
        OBSERVABLES[1]: -11.25,
        OBSERVABLES[2]: 0.1,
    }),)
    report = ReportBuilder().build(SimpleNamespace(name="fixture"), context)
    ConsoleReporter().print(report)
    output = capsys.readouterr().out
    assert "Deterministic reflection experiment comparisons" in output
    assert "Status: CHANGE_OBSERVED" in output
    assert "delta -3.25" in output
    assert "Causality: NOT_ESTABLISHED" in output
    assert "Ranking impact: NONE" in output
    assert "Recommendation impact: NONE" in output
    assert "Eligibility impact: NONE" in output


def test_traceability_preserves_proposal_declaration_comparison_chain_only():
    item = comparison()
    link = TraceabilityEngine._reflection_experiment_comparison_graph((item,))[0]
    assert link.verification_proposal_codes == (item.proposal_id,)
    assert link.experiment_declaration_codes == (item.experiment_declaration_id,)
    assert link.experiment_comparison_codes == (item.comparison_id,)
    assert link.hypothesis_codes == ()
    assert link.ranking_codes == ()
    assert link.recommendation_codes == ()
    assert link.recommended_candidate_codes == ()


def test_engine_has_no_llm_hidden_measurement_or_upstream_decision_access():
    source = getsource(DeterministicReflectionExperimentComparisonEngine).lower()
    for forbidden in (
        "openai", "ollama", "get_measurement", "impulseresponse",
        "acousticreasoning", "recommendationengine", "experimentplanner",
    ):
        assert forbidden not in source
    root = Path(__file__).resolve().parents[1]
    for relative in (
        "acousticbrain/analysis/acoustic_reasoning.py",
        "acousticbrain/analysis/experiment_planning.py",
        "acousticbrain/analysis/recommendation.py",
        "acousticbrain/analysis/reflection_verification_planning.py",
    ):
        assert "DeterministicReflectionExperimentComparison" not in (
            root / relative
        ).read_text()
