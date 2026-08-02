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


def test_preview_cli_is_read_only_and_prints_projected_decisions(tmp_path, capsys):
    value = record(EvidencePlanPrerequisiteStatus.CONFIRMED, EvidencePlanPrerequisiteStatus.UNKNOWN)
    path = tmp_path / "registry.json"
    repository = EvidencePlanPreparationRegistryJsonRepository()
    repository.save(path, EvidencePlanPreparationRegistry())
    before = path.read_bytes()
    result = acousticbrain_main.preview_evidence_plan_preparation(
        tmp_path, value.confirmation_input, path, brain=Brain()
    )
    output = capsys.readouterr().out
    assert result.registry_state == "NOT_RECORDED"
    assert "PREPARATION_DECLARED" in output
    assert "ALL_PREREQUISITES_USER_CONFIRMED : indisponible" in output
    assert "Aucune préparation enregistrée" in output
    assert path.read_bytes() == before


def test_preview_parser_requires_explicit_registry(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--preview-evidence-plan-preparation", str(tmp_path / "draft.json"),
        ))
    assert "requires --evidence-plan-preparation-registry" in capsys.readouterr().err
