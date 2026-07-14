from dataclasses import fields, replace
from inspect import getsource
from types import SimpleNamespace

import pytest

from acousticbrain.analysis import AnalysisContext, TraceabilityEngine
from acousticbrain.application import ControlledReflectionExperimentDeclarationService
from acousticbrain.brain.builders.report import ReportBuilder
from acousticbrain.brain.pipeline import BrainPipeline
from acousticbrain.brain.stages.reflection_experiment_declaration import (
    ControlledReflectionExperimentDeclarationStage,
)
from acousticbrain.models import (
    ControlledReflectionExperimentDeclaration,
    ControlledReflectionExperimentDeclarationRegistry,
    ControlledReflectionVerificationPlanningAnalysis,
    Measurement,
    ReflectionCandidateVerificationProposal,
    ReflectionDeclarationProvenanceSource,
    ReflectionExperimentDeclarationStatus,
    ReflectionVerificationCausalityStatus,
    ReflectionVerificationExecutionStatus,
    ReflectionVerificationImpact,
    ReflectionVerificationMethod,
)
from acousticbrain.persistence import (
    ControlledReflectionExperimentJsonCodec,
    ControlledReflectionExperimentJsonRepository,
)
from acousticbrain.report import ConsoleReporter


PROPOSAL_ID = (
    "reflection_verification_proposal."
    "material_reflection_candidate.correlation.front"
)


def proposal(proposal_id=PROPOSAL_ID):
    return ReflectionCandidateVerificationProposal(
        proposal_id=proposal_id,
        source_candidate_id="material_reflection_candidate.correlation.front",
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
        controlled_variable_codes=("MICROPHONE_POSITION", "MEASUREMENT_LEVEL"),
        changed_variable_codes=("TEMPORARY_MASK_STATE",),
        observable_fact_codes=("ETC_EVENT_RELATIVE_LEVEL_DB",),
        supporting_outcome_codes=("REFLECTION_DECREASES_AFTER_MASKING",),
        counter_outcome_codes=("REFLECTION_REMAINS_UNCHANGED_AFTER_MASKING",),
        source_evidence_codes=("evidence.candidate.front",),
        source_provenance_codes=("GEOMETRY-SOURCE",),
        planning_rule_codes=("CONTROLLED_TEMPORARY_MASK",),
        execution_status=ReflectionVerificationExecutionStatus.NOT_EXECUTED,
        causality_status=ReflectionVerificationCausalityStatus.NOT_ESTABLISHED,
        eligibility_impact=ReflectionVerificationImpact.NONE,
        recommendation_impact=ReflectionVerificationImpact.NONE,
        limitations=("CAUSALITY_NOT_ESTABLISHED",),
    )


def planning(*proposals):
    return ControlledReflectionVerificationPlanningAnalysis(
        proposals=tuple(proposals or (proposal(),)),
        exclusions=(),
        source_analysis_codes=("MaterialAwareReflectionCandidateAnalysis",),
        applied_rule_codes=("CONTROLLED_TEMPORARY_MASK",),
    )


def measurement(reference_id, experiment_id):
    return ControlledReflectionExperimentDeclarationService.measurement_reference(
        reference_id=reference_id,
        experiment_id=experiment_id,
        measurement_name="stereo",
        manifest_id=f"manifest.{experiment_id}",
        content_hash=f"sha256:{reference_id}",
    )


def declaration(
    status=ReflectionExperimentDeclarationStatus.PLANNED,
    *,
    proposal_id=PROPOSAL_ID,
):
    executed = status is ReflectionExperimentDeclarationStatus.EXECUTED
    reason = (
        f"{status.value}_BY_OPERATOR"
        if status in {
            ReflectionExperimentDeclarationStatus.INVALID,
            ReflectionExperimentDeclarationStatus.CANCELLED,
        }
        else None
    )
    return ControlledReflectionExperimentDeclarationService().declare(
        planning(proposal(proposal_id)),
        proposal_id=proposal_id,
        status=status,
        declarer_id="operator.seb",
        reference_measurements=(measurement("baseline", "exp-010"),) if executed else (),
        intervention_measurements=(measurement("masked", "exp-011"),) if executed else (),
        status_reason_code=reason,
    )


def test_declaration_is_linked_to_an_existing_pr036_proposal():
    result = declaration()
    assert result.proposal_id == PROPOSAL_ID
    assert result.declaration_id == f"reflection_experiment_declaration.{PROPOSAL_ID}"
    with pytest.raises(ValueError, match="existing proposal"):
        ControlledReflectionExperimentDeclarationService().declare(
            planning(),
            proposal_id="reflection_verification_proposal.unknown",
            status=ReflectionExperimentDeclarationStatus.PLANNED,
            declarer_id="operator.seb",
        )
    with pytest.raises(ValueError, match="PR-036 planning analysis"):
        ControlledReflectionExperimentDeclarationService().declare(
            SimpleNamespace(proposals=(proposal(),)),
            proposal_id=PROPOSAL_ID,
            status=ReflectionExperimentDeclarationStatus.PLANNED,
            declarer_id="operator.seb",
        )


def test_conditions_are_inherited_exactly_without_mutating_the_proposal():
    source = planning()
    before = repr(source)
    result = ControlledReflectionExperimentDeclarationService().declare(
        source,
        proposal_id=PROPOSAL_ID,
        status=ReflectionExperimentDeclarationStatus.PLANNED,
        declarer_id="operator.seb",
    )
    assert result.reference_condition.condition_code == "UNMASKED_REFERENCE"
    assert result.intervention_condition.condition_code == "TEMPORARY_MASK_APPLIED"
    assert repr(source) == before


def test_status_vocabulary_is_closed_and_non_interpretive():
    assert tuple(item.value for item in ReflectionExperimentDeclarationStatus) == (
        "PLANNED", "EXECUTED", "INVALID", "CANCELLED"
    )
    names = {field.name for field in fields(ControlledReflectionExperimentDeclaration)}
    assert names.isdisjoint({
        "result", "comparison", "hypothesis_status", "causal_conclusion",
        "score", "rank", "priority", "recommendation", "eligible",
    })


def test_executed_means_measurement_sets_exist_and_nothing_more():
    result = declaration(ReflectionExperimentDeclarationStatus.EXECUTED)
    assert result.status is ReflectionExperimentDeclarationStatus.EXECUTED
    assert len(result.reference_condition.measurement_references) == 1
    assert len(result.intervention_condition.measurement_references) == 1
    with pytest.raises(ValueError, match="both measurement conditions"):
        replace(result, intervention_condition=declaration().intervention_condition)


@pytest.mark.parametrize(
    "status",
    [
        ReflectionExperimentDeclarationStatus.INVALID,
        ReflectionExperimentDeclarationStatus.CANCELLED,
    ],
)
def test_terminal_non_execution_statuses_require_an_explicit_reason(status):
    result = declaration(status)
    assert result.status_reason_code == f"{status.value}_BY_OPERATOR"
    with pytest.raises(ValueError, match="reason is inconsistent"):
        replace(result, status_reason_code=None)


def test_planned_and_executed_reject_status_reasons():
    with pytest.raises(ValueError, match="reason is inconsistent"):
        replace(declaration(), status_reason_code="UNEXPECTED")


def test_measurement_reference_provenance_is_manifest_only_and_complete():
    reference = measurement("baseline", "exp-010")
    assert {item.field_code for item in reference.field_provenance} == {
        "reference_id", "experiment_id", "measurement_name", "content_hash"
    }
    assert {
        item.source for item in reference.field_provenance
    } == {ReflectionDeclarationProvenanceSource.MEASUREMENT_MANIFEST}


def test_every_declaration_and_condition_field_has_separate_provenance():
    result = declaration(ReflectionExperimentDeclarationStatus.EXECUTED)
    assert {item.field_code for item in result.field_provenance} == {
        "declaration_id", "proposal_id", "status",
        "reference_condition", "intervention_condition",
    }
    for condition in (result.reference_condition, result.intervention_condition):
        assert {item.field_code for item in condition.field_provenance} == {
            "condition_code", "measurement_references"
        }


def test_same_measurement_cannot_be_declared_in_both_conditions():
    shared = measurement("shared", "exp-010")
    with pytest.raises(ValueError, match="both conditions"):
        ControlledReflectionExperimentDeclarationService().declare(
            planning(),
            proposal_id=PROPOSAL_ID,
            status=ReflectionExperimentDeclarationStatus.EXECUTED,
            declarer_id="operator.seb",
            reference_measurements=(shared,),
            intervention_measurements=(shared,),
        )


def test_registry_rejects_multiple_declarations_for_one_proposal():
    item = declaration()
    with pytest.raises(ValueError, match="unique per proposal"):
        ControlledReflectionExperimentDeclarationRegistry((item, item))


def test_json_round_trip_is_deterministic_and_sorted():
    first = declaration()
    second = declaration(
        ReflectionExperimentDeclarationStatus.CANCELLED,
        proposal_id=(
            "reflection_verification_proposal."
            "material_reflection_candidate.correlation.side"
        ),
    )
    codec = ControlledReflectionExperimentJsonCodec()
    registry = ControlledReflectionExperimentDeclarationRegistry((second, first))
    payload = codec.dumps(registry)
    assert codec.loads(payload) == ControlledReflectionExperimentDeclarationRegistry(
        (first, second)
    )
    assert payload == codec.dumps(codec.loads(payload))
    assert payload.index(first.declaration_id) < payload.index(second.declaration_id)


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "[]",
        '{"schema_version": 2, "declarations": []}',
        '{"schema_version": 1, "declarations": {}}',
    ],
)
def test_json_codec_rejects_invalid_or_unknown_payloads(payload):
    with pytest.raises(ValueError):
        ControlledReflectionExperimentJsonCodec().loads(payload)


def test_repository_is_atomic_idempotent_and_missing_file_is_empty(tmp_path):
    path = tmp_path / "reflection-experiments.json"
    repository = ControlledReflectionExperimentJsonRepository()
    assert repository.load(path).declarations == ()
    registry = ControlledReflectionExperimentDeclarationRegistry((declaration(),))
    assert repository.save(path, registry) is True
    assert repository.save(path, registry) is False
    assert repository.load(path) == registry
    assert not path.with_suffix(".json.tmp").exists()


def test_service_explicitly_loads_persisted_declarations_into_project(tmp_path):
    path = tmp_path / "reflection-experiments.json"
    service = ControlledReflectionExperimentDeclarationService()
    service.save(path, (declaration(),))
    project = SimpleNamespace(controlled_reflection_experiment_declarations=())
    registry = service.load_into_project(project, path)
    assert project.controlled_reflection_experiment_declarations == registry.declarations


def test_stage_copies_only_explicit_project_declarations_in_stable_order():
    first = declaration()
    second = declaration(
        ReflectionExperimentDeclarationStatus.CANCELLED,
        proposal_id=(
            "reflection_verification_proposal."
            "material_reflection_candidate.correlation.side"
        ),
    )
    project = SimpleNamespace(
        controlled_reflection_experiment_declarations=(second, first)
    )
    context = AnalysisContext(Measurement("stereo"))
    ControlledReflectionExperimentDeclarationStage().run(project, context)
    assert context.controlled_reflection_experiment_declarations == (first, second)


def test_pipeline_places_declarations_after_pr036_and_before_reasoning():
    source = getsource(BrainPipeline.run)
    assert source.index("ControlledReflectionVerificationPlanningStage().run") < (
        source.index("ControlledReflectionExperimentDeclarationStage().run")
    ) < source.index("AcousticReasoningStage().run")


def test_presenter_and_console_publish_declaration_without_interpretation(capsys):
    context = AnalysisContext(Measurement("stereo"))
    context.controlled_reflection_experiment_declarations = (
        declaration(ReflectionExperimentDeclarationStatus.EXECUTED),
    )
    report = ReportBuilder().build(SimpleNamespace(name="fixture"), context)
    ConsoleReporter().print(report)
    output = capsys.readouterr().out
    assert "Controlled reflection experiment declarations" in output
    assert "Status: EXECUTED" in output
    assert "Baseline condition: UNMASKED_REFERENCE" in output
    assert "Intervention condition: TEMPORARY_MASK_APPLIED" in output
    assert "Result interpretation: NONE" in output
    assert "Causality: NOT_ESTABLISHED" in output
    assert "Ranking impact: NONE" in output
    assert "Recommendation impact: NONE" in output


def test_traceability_links_declaration_to_proposal_without_decision_claims():
    item = declaration(ReflectionExperimentDeclarationStatus.EXECUTED)
    link = TraceabilityEngine._reflection_experiment_declaration_graph((item,))[0]
    assert link.experiment_declaration_codes == (item.declaration_id,)
    assert link.verification_proposal_codes == (item.proposal_id,)
    assert link.fact_codes == ()
    assert link.evidence_codes == ()
    assert link.hypothesis_codes == ()
    assert link.ranking_codes == ()
    assert link.recommendation_codes == ()
    assert link.recommended_candidate_codes == ()


def test_declaration_layer_has_no_llm_or_upstream_decision_dependency():
    service_source = getsource(ControlledReflectionExperimentDeclarationService).lower()
    assert "openai" not in service_source
    assert "ollama" not in service_source
    root = __file__.rsplit("/tests/", 1)[0]
    for relative in (
        "acousticbrain/analysis/acoustic_reasoning.py",
        "acousticbrain/analysis/experiment_planning.py",
        "acousticbrain/analysis/recommendation.py",
        "acousticbrain/analysis/reflection_verification_planning.py",
    ):
        with open(f"{root}/{relative}", encoding="utf-8") as handle:
            upstream = handle.read()
        assert "ControlledReflectionExperimentDeclaration" not in upstream
