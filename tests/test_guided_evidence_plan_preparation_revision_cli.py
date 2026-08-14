from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.models import EvidencePlanPreparationRegistry, EvidencePlanPrerequisiteStatus
from acousticbrain.persistence import EvidencePlanPreparationConfirmationJsonLoader, EvidencePlanPreparationRegistryJsonRepository
from test_evidence_plan_preparation_resolution import confirmation, ready_plan


class Brain:
    def analyze(self, **arguments):
        return object(), SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(ready_plan(),))
        )


def test_status_parser_is_closed_and_rejects_duplicates():
    assert acousticbrain_main.parse_preparation_statuses((
        "documented_microphone_position=CONFIRMED",
        "existing_acquisition_settings=UNKNOWN",
    )) == {
        "documented_microphone_position": EvidencePlanPrerequisiteStatus.CONFIRMED,
        "existing_acquisition_settings": EvidencePlanPrerequisiteStatus.UNKNOWN,
    }
    with pytest.raises(ValueError, match="Duplicate"):
        acousticbrain_main.parse_preparation_statuses(("a=UNKNOWN", "a=CONFIRMED"))
    with pytest.raises(ValueError, match="Invalid"):
        acousticbrain_main.parse_preparation_statuses(("a=YES",))


def test_cli_revision_writes_only_new_draft_and_preserves_source_registry(tmp_path, capsys):
    plan = ready_plan()
    source = confirmation(plan)
    source_path = tmp_path / "source.json"
    codec = EvidencePlanPreparationConfirmationJsonLoader()
    codec.save_new(source_path, source)
    registry_path = tmp_path / "registry.json"
    repository = EvidencePlanPreparationRegistryJsonRepository()
    repository.save(registry_path, EvidencePlanPreparationRegistry())
    source_before = source_path.read_bytes()
    registry_before = registry_path.read_bytes()
    output = tmp_path / "revised.json"
    acousticbrain_main.revise_evidence_plan_preparation(
        tmp_path, source,
        {
            "documented_microphone_position": EvidencePlanPrerequisiteStatus.CONFIRMED,
            "existing_acquisition_settings": EvidencePlanPrerequisiteStatus.UNKNOWN,
        },
        registry_path, output, brain=Brain(), registry_repository=repository,
    )
    revised = codec.load(output)
    assert revised.confirmation_id != source.confirmation_id
    assert revised.prerequisites[0].status is EvidencePlanPrerequisiteStatus.CONFIRMED
    assert revised.prerequisites[1].status is EvidencePlanPrerequisiteStatus.UNKNOWN
    assert source_path.read_bytes() == source_before
    assert registry_path.read_bytes() == registry_before
    assert "Aucune préparation enregistrée" in capsys.readouterr().out
