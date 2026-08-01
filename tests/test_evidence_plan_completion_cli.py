from pathlib import Path
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.application import EvidencePlanCompletionWorkflowResult
from acousticbrain.models import EvidencePlanCompletionRegistry
from test_evidence_plan_completion_registry import record
from test_derived_evidence_plan import protocol_compatibility
from test_evidence_plan_completion_resolution import blocking_factor


class ContextBrain:
    def __init__(self, context):
        self.context = context
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return object(), self.context


class RecordingCompletionService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def complete(self, completion_input, **arguments):
        self.calls.append((completion_input, arguments))
        return self.result


class EmptyRegistryRepository:
    def load(self, path):
        return EvidencePlanCompletionRegistry()


def completion_context(value):
    derived = value.derived_plan
    source = derived.source_plan
    factor = SimpleNamespace(factor_id=source.blocking_factor_ids[0])
    action = SimpleNamespace(action_id=source.corrective_action_id)
    protocol = SimpleNamespace(protocol_id=derived.reference_id)
    return SimpleNamespace(
        evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(source,)),
        deterministic_evidence_weighting_synthesis=SimpleNamespace(
            weights=(SimpleNamespace(blocking_factors=(factor,)),)
        ),
        deterministic_corrective_action_synthesis=SimpleNamespace(
            actions=(action,)
        ),
        listening_position_sampling_protocol=protocol,
    )


def workflow_result(value, path, *, persisted=True):
    return EvidencePlanCompletionWorkflowResult(
        record=value,
        registry_path=str(path),
        persisted=persisted,
    )


def test_parser_accepts_explicit_completion_paths():
    arguments = acousticbrain_main.create_parser().parse_args((
        "--complete-evidence-plan", "completion.json",
        "--evidence-plan-completion-registry", "state/completions.json",
    ))
    assert arguments.complete_evidence_plan == Path("completion.json")
    assert arguments.evidence_plan_completion_registry == Path(
        "state/completions.json"
    )


def test_completion_cli_routes_exact_typed_analysis_objects(tmp_path, capsys):
    value = record()
    path = tmp_path / "completion-registry.json"
    context = completion_context(value)
    brain = ContextBrain(context)
    service = RecordingCompletionService(workflow_result(value, path))

    result = acousticbrain_main.complete_evidence_plan(
        tmp_path,
        value.completion_input,
        path,
        brain=brain,
        service=service,
        registry_repository=EmptyRegistryRepository(),
    )

    assert result.record == value
    assert brain.calls == [{
        "measurement_root": tmp_path,
        "compare_experiments": True,
        "analyze_causal_discrimination": True,
        "synthesize_evidence_acquisition": True,
        "listening_position_campaign_instance_analysis": None,
        "return_context": True,
    }]
    _, routed = service.calls[0]
    assert routed["source_plans"] is context.evidence_acquisition_plan_synthesis.plans
    assert routed["blocking_factors"] == (
        context.deterministic_evidence_weighting_synthesis.weights[0]
        .blocking_factors[0],
    )
    assert routed["actions"] is (
        context.deterministic_corrective_action_synthesis.actions
    )
    assert routed["protocol_references"] == (
        context.listening_position_sampling_protocol,
    )
    assert "REFERENCE_RESOLVED" in capsys.readouterr().out


def test_main_loads_one_input_and_exits_without_standard_reporting(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()
    input_path = tmp_path / "completion.json"
    input_path.write_text("{}", encoding="utf-8")
    registry_path = tmp_path / "completion-registry.json"
    value = record()
    loader = SimpleNamespace(load=lambda path: value.completion_input)
    service = RecordingCompletionService(workflow_result(value, registry_path))
    brain = ContextBrain(completion_context(value))

    result = acousticbrain_main.main(
        (
            "--measurements-root", str(root),
            "--complete-evidence-plan", str(input_path),
            "--evidence-plan-completion-registry", str(registry_path),
        ),
        brain=brain,
        evidence_plan_completion_loader=loader,
        evidence_plan_completion_service=service,
        evidence_plan_completion_registry_repository=(
            EmptyRegistryRepository()
        ),
    )

    assert result == 0
    assert len(service.calls) == 1


def test_completion_requires_an_explicit_registry(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--complete-evidence-plan", str(tmp_path / "completion.json"),
        ))
    assert error.value.code == 2
    assert "requires --evidence-plan-completion-registry" in (
        capsys.readouterr().err
    )


def test_completion_rejects_reporting_modes_before_analysis(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    brain = ContextBrain(SimpleNamespace())
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--complete-evidence-plan", str(tmp_path / "completion.json"),
            "--evidence-plan-completion-registry", str(tmp_path / "registry.json"),
            "--full-assessment",
        ), brain=brain)
    assert brain.calls == []
    assert "cannot be combined with --full-assessment" in capsys.readouterr().err


def test_completion_refuses_missing_typed_analysis_contracts(tmp_path):
    with pytest.raises(ValueError, match="analysis contracts are unavailable"):
        acousticbrain_main.complete_evidence_plan(
            tmp_path,
            record().completion_input,
            tmp_path / "registry.json",
            brain=ContextBrain(SimpleNamespace()),
        )


def test_cli_boundary_runs_the_real_transactional_service(tmp_path):
    compatibility = protocol_compatibility()
    context = SimpleNamespace(
        evidence_acquisition_plan_synthesis=SimpleNamespace(
            plans=(compatibility.resolution.source_plan,)
        ),
        deterministic_evidence_weighting_synthesis=SimpleNamespace(
            weights=(SimpleNamespace(blocking_factors=(blocking_factor(),)),)
        ),
        deterministic_corrective_action_synthesis=SimpleNamespace(
            actions=(compatibility.source_action,)
        ),
        listening_position_sampling_protocol=compatibility.resolution.reference,
    )
    registry_path = tmp_path / "state" / "completion-registry.json"

    result = acousticbrain_main.complete_evidence_plan(
        tmp_path,
        compatibility.resolution.completion_input,
        registry_path,
        brain=ContextBrain(context),
    )

    assert result.persisted is True
    assert registry_path.is_file()
    assert result.record.derived_plan.source_plan == (
        compatibility.resolution.source_plan
    )
