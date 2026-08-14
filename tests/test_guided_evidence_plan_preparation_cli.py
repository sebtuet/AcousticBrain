from pathlib import Path
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.models import EvidencePlanPreparationRegistry
from acousticbrain.persistence import EvidencePlanPreparationRegistryJsonRepository
from test_evidence_plan_preparation_resolution import ready_plan


class ContextBrain:
    def __init__(self, plans):
        self.plans = plans
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return object(), SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(plans=self.plans)
        )


def test_parser_accepts_guided_generation_paths():
    arguments = acousticbrain_main.create_parser().parse_args((
        "--generate-evidence-plan-preparation", "READY_PLAN",
        "--evidence-plan-preparation-registry", "state/preparations.json",
        "--evidence-plan-preparation-output", "draft.json",
    ))
    assert arguments.generate_evidence_plan_preparation == "READY_PLAN"
    assert arguments.evidence_plan_preparation_output == Path("draft.json")


def test_preview_prints_unknown_json_without_writing(tmp_path, capsys):
    registry_path = tmp_path / "registry.json"
    EvidencePlanPreparationRegistryJsonRepository().save(
        registry_path, EvidencePlanPreparationRegistry()
    )
    before = registry_path.read_bytes()
    result = acousticbrain_main.generate_evidence_plan_preparation(
        tmp_path,
        "READY_PLAN",
        registry_path,
        brain=ContextBrain((ready_plan(),)),
    )
    output = capsys.readouterr().out
    assert result.confirmation_input.confirmation_id.endswith("-1")
    assert "documented_microphone_position : UNKNOWN" in output
    assert '"status": "UNKNOWN"' in output
    assert "Brouillon non écrit" in output
    assert "Aucune préparation enregistrée" in output
    assert registry_path.read_bytes() == before


def test_explicit_output_creates_reloadable_draft_only(tmp_path, capsys):
    registry_path = tmp_path / "registry.json"
    repository = EvidencePlanPreparationRegistryJsonRepository()
    repository.save(registry_path, EvidencePlanPreparationRegistry())
    output_path = tmp_path / "draft.json"
    acousticbrain_main.generate_evidence_plan_preparation(
        tmp_path,
        "READY_PLAN",
        registry_path,
        output_path=output_path,
        brain=ContextBrain((ready_plan(),)),
    )
    assert output_path.is_file()
    assert repository.load(registry_path) == EvidencePlanPreparationRegistry()
    assert "Brouillon écrit" in capsys.readouterr().out


def test_generation_requires_registry_and_rejects_other_modes(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--generate-evidence-plan-preparation", "READY_PLAN",
        ))
    assert "requires --evidence-plan-preparation-registry" in capsys.readouterr().err
    brain = ContextBrain(())
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--generate-evidence-plan-preparation", "READY_PLAN",
            "--evidence-plan-preparation-registry", str(tmp_path / "registry.json"),
            "--full-assessment",
        ), brain=brain)
    assert brain.calls == []
    assert "cannot be combined with --full-assessment" in capsys.readouterr().err


def test_output_option_requires_generation(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--evidence-plan-preparation-output", str(tmp_path / "draft.json"),
        ))
    assert "requires --generate-evidence-plan-preparation" in capsys.readouterr().err
