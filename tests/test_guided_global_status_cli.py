from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.models import (
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan
from test_guided_global_status_presenter import report_for


class Brain:
    def analyze(self, **arguments):
        plan = ready_plan()
        return report_for(plan), SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(plan,))
        )


class Repository:
    def __init__(self, registry):
        self.registry = registry
        self.loaded = []

    def load(self, path):
        self.loaded.append(path)
        return self.registry


def test_cli_shows_real_incomplete_preparation_without_writing(tmp_path, capsys):
    registry_path = tmp_path / "preparations.json"
    registry_path.write_text("preserve\n", encoding="utf-8")
    registry = EvidencePlanPreparationRegistry().with_record(record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    ))
    repository = Repository(registry)
    before = tuple(path.read_bytes() for path in tmp_path.iterdir())
    result = acousticbrain_main.show_guided_status(
        tmp_path,
        registry_path,
        None,
        brain=Brain(),
        registry_repository=repository,
    )
    output = capsys.readouterr().out
    assert result.workflow_state == "READY_PLAN_PREPARATION_INCOMPLETE"
    assert "existing_acquisition_settings=UNKNOWN" in output
    assert output.count("Action utilisateur") == 1
    assert "Causality status: NOT_ESTABLISHED" in output
    assert repository.loaded == [registry_path]
    assert tuple(path.read_bytes() for path in tmp_path.iterdir()) == before


def test_cli_without_registry_does_not_attempt_discovery(tmp_path, capsys):
    result = acousticbrain_main.show_guided_status(tmp_path, brain=Brain())
    assert result.workflow_state == "READY_PLAN_PREPARATION_UNAVAILABLE"
    assert "aucun registre explicite fourni" in capsys.readouterr().out


def test_main_rejects_guided_registry_without_guided_status(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--guided-preparation-registry", str(tmp_path / "registry.json"),
        ))
    assert "requires --guided-status" in capsys.readouterr().err


def test_main_requires_registry_for_explicit_guided_preparation(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--guided-status",
            "--guided-preparation", "preparation-001",
        ))
    assert "requires --guided-preparation-registry" in capsys.readouterr().err


@pytest.mark.parametrize(
    "option",
    (
        "--full-assessment",
        "--evidence-plan-overview",
        "--exploratory",
    ),
)
def test_main_rejects_guided_status_combined_with_other_modes(
    tmp_path, capsys, option
):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--guided-status",
            option,
        ))
    assert f"cannot be combined with {option}" in capsys.readouterr().err
