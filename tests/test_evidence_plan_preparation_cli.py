from pathlib import Path
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.application import EvidencePlanPreparationWorkflowResult
from acousticbrain.models import (
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan


def preparation_record():
    return record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )


class ContextBrain:
    def __init__(self, context):
        self.context = context
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return object(), self.context


class RecordingPreparationService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def record(self, confirmation_input, **arguments):
        self.calls.append((confirmation_input, arguments))
        return self.result


class EmptyRegistryRepository:
    def load(self, path):
        return EvidencePlanPreparationRegistry()


def workflow_result(value, path, *, persisted=True):
    return EvidencePlanPreparationWorkflowResult(
        record=value,
        registry_path=str(path),
        persisted=persisted,
    )


def test_parser_accepts_explicit_preparation_paths():
    arguments = acousticbrain_main.create_parser().parse_args((
        "--confirm-evidence-plan-preparation", "preparation.json",
        "--evidence-plan-preparation-registry", "state/preparations.json",
    ))
    assert arguments.confirm_evidence_plan_preparation == Path("preparation.json")
    assert arguments.evidence_plan_preparation_registry == Path(
        "state/preparations.json"
    )


def test_preparation_cli_routes_exact_plans_and_prints_separate_decisions(
    tmp_path, capsys
):
    value = preparation_record()
    plan = ready_plan()
    path = tmp_path / "preparation-registry.json"
    brain = ContextBrain(SimpleNamespace(
        evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(plan,))
    ))
    service = RecordingPreparationService(workflow_result(value, path))

    result = acousticbrain_main.confirm_evidence_plan_preparation(
        tmp_path,
        value.confirmation_input,
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
    assert service.calls[0][1]["plans"] == (plan,)
    output = capsys.readouterr().out
    assert "PLAN_EXACTLY_RESOLVED" in output
    assert "PREPARATION_DECLARED" in output
    assert "ALL_PREREQUISITES_USER_CONFIRMED: unavailable" in output
    assert "No experiment was declared or executed." in output


def test_main_loads_one_input_and_exits_without_standard_reporting(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()
    input_path = tmp_path / "preparation.json"
    input_path.write_text("{}", encoding="utf-8")
    registry_path = tmp_path / "preparation-registry.json"
    value = preparation_record()
    loader = SimpleNamespace(load=lambda path: value.confirmation_input)
    service = RecordingPreparationService(workflow_result(value, registry_path))
    plan = ready_plan()
    brain = ContextBrain(SimpleNamespace(
        evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(plan,))
    ))

    result = acousticbrain_main.main((
        "--measurements-root", str(root),
        "--confirm-evidence-plan-preparation", str(input_path),
        "--evidence-plan-preparation-registry", str(registry_path),
    ), brain=brain, evidence_plan_preparation_loader=loader,
       evidence_plan_preparation_service=service,
       evidence_plan_preparation_registry_repository=EmptyRegistryRepository())

    assert result == 0
    assert len(service.calls) == 1


def test_preparation_requires_an_explicit_registry(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--confirm-evidence-plan-preparation", str(tmp_path / "input.json"),
        ))
    assert error.value.code == 2
    assert "requires --evidence-plan-preparation-registry" in (
        capsys.readouterr().err
    )


def test_preparation_rejects_reporting_modes_before_analysis(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    brain = ContextBrain(SimpleNamespace())
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--confirm-evidence-plan-preparation", str(tmp_path / "input.json"),
            "--evidence-plan-preparation-registry", str(tmp_path / "registry.json"),
            "--full-assessment",
        ), brain=brain)
    assert brain.calls == []
    assert "cannot be combined with --full-assessment" in capsys.readouterr().err


def test_preparation_refuses_missing_typed_analysis_contracts(tmp_path):
    with pytest.raises(ValueError, match="analysis contracts are unavailable"):
        acousticbrain_main.confirm_evidence_plan_preparation(
            tmp_path,
            preparation_record().confirmation_input,
            tmp_path / "registry.json",
            brain=ContextBrain(SimpleNamespace()),
        )
