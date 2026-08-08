from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.models import (
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan


class Brain:
    def analyze(self, **arguments):
        return object(), SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(ready_plan(),))
        )


class Repository:
    def __init__(self, registry):
        self.registry = registry

    def load(self, path):
        return self.registry


def confirmed_registry():
    return EvidencePlanPreparationRegistry().with_record(record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    ))


def test_cli_renders_only_the_separate_existing_declaration_command(tmp_path, capsys):
    (tmp_path / "baseline").mkdir()
    registry = confirmed_registry()
    confirmation_id = registry.records[0].confirmation_input.confirmation_id
    before = tuple(path.name for path in tmp_path.iterdir())
    result = acousticbrain_main.show_channel_isolation_declaration_readiness(
        tmp_path,
        "READY_PLAN",
        confirmation_id,
        tmp_path / "registry.json",
        "baseline",
        "channel-isolation-001",
        brain=Brain(),
        registry_repository=Repository(registry),
    )
    output = capsys.readouterr().out
    assert result.statuses[-1] == "DECLARATION_READY"
    assert output.count("Action utilisateur") == 1
    assert "python -m acousticbrain.commands.declare_evidence_plan_experiment" in output
    assert "DECLARATION_READY ne signifie pas EXECUTED" in output
    assert tuple(path.name for path in tmp_path.iterdir()) == before
    assert not (tmp_path / "channel-isolation-001").exists()


def test_main_requires_every_readiness_input(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--channel-isolation-declaration-readiness", "READY_PLAN",
        ))
    error = capsys.readouterr().err
    assert "--channel-isolation-preparation" in error
    assert "--channel-isolation-reference" in error
    assert "--channel-isolation-experiment" in error
