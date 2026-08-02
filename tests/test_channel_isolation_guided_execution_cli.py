from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.models import EvidencePlanPreparationRegistry, EvidencePlanPrerequisiteStatus
from acousticbrain.persistence import EvidencePlanPreparationRegistryJsonRepository
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan


class Brain:
    def analyze(self, **arguments):
        return object(), SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(ready_plan(),))
        )


def test_cli_renders_complete_read_only_checklist_for_incomplete_preparation(tmp_path, capsys):
    preparation = record(EvidencePlanPrerequisiteStatus.CONFIRMED, EvidencePlanPrerequisiteStatus.UNKNOWN)
    path = tmp_path / "registry.json"
    repository = EvidencePlanPreparationRegistryJsonRepository()
    repository.save(path, EvidencePlanPreparationRegistry().with_record(preparation))
    before = path.read_bytes()
    journey = acousticbrain_main.show_channel_isolation_journey(
        tmp_path, "READY_PLAN", preparation.confirmation_input.confirmation_id,
        path, brain=Brain(), registry_repository=repository,
    )
    output = capsys.readouterr().out
    assert journey.preparation_status == "PREPARATION_INCOMPLETE"
    assert "Canaux à acquérir : LEFT, RIGHT" in output
    assert "Canaux à répéter : LEFT, RIGHT" in output
    assert "Aide aux prérequis" in output
    assert "CONFIRMED si :" in output
    assert "UNKNOWN si :" in output
    assert "aucune déclaration d’expérience n’est disponible" in output
    assert "Causality status: NOT_ESTABLISHED" in output
    assert path.read_bytes() == before


def test_cli_requires_explicit_preparation_and_registry(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--channel-isolation-journey", "READY_PLAN",
        ))
    assert "requires --channel-isolation-preparation" in capsys.readouterr().err
