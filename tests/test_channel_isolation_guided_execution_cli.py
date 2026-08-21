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


def test_cli_routes_confirmed_preparation_to_public_declaration_preflight(
    tmp_path, capsys
):
    preparation = record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    path = tmp_path / "registry.json"
    repository = EvidencePlanPreparationRegistryJsonRepository()
    repository.save(path, EvidencePlanPreparationRegistry().with_record(preparation))
    before = path.read_bytes()

    journey = acousticbrain_main.show_channel_isolation_journey(
        tmp_path,
        "READY_PLAN",
        preparation.confirmation_input.confirmation_id,
        path,
        brain=Brain(),
        registry_repository=repository,
    )

    output = capsys.readouterr().out
    assert journey.preparation_status == "PREPARATION_USER_CONFIRMED"
    assert "--channel-isolation-declaration-readiness READY_PLAN" in output
    assert (
        "--channel-isolation-preparation "
        + preparation.confirmation_input.confirmation_id
        in output
    )
    assert f"--evidence-plan-preparation-registry {path}" in output
    assert "préflight" in output
    assert "ne les choisit pas à votre place" in output
    assert "--channel-isolation-reference <EXPERIENCE_REFERENCE_EXISTANTE>" in output
    assert "--channel-isolation-experiment <NOUVEL_ID_EXPERIENCE>" in output
    assert "Aucune expérience n’a été déclarée ou exécutée" in output
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
