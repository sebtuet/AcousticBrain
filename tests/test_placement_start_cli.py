from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.models import EvidencePlanPreparationRegistry
from acousticbrain.persistence import EvidencePlanPreparationRegistryJsonRepository
from test_evidence_plan_preparation_resolution import ready_plan


class ContextBrain:
    def __init__(self, plans):
        self.context = SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(plans=plans)
        )
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return object(), self.context


def answers(*values):
    values = iter(values)
    return lambda prompt: next(values)


def test_start_placement_records_only_after_explicit_confirmation(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    brain = ContextBrain((ready_plan(),))

    result = acousticbrain_main.main(
        ("--measurements-root", str(root), "--start-placement"),
        brain=brain,
        placement_input=answers("o", "i", "o"),
    )

    registry_path = root / acousticbrain_main.DEFAULT_PLACEMENT_PREPARATION_REGISTRY
    registry = EvidencePlanPreparationRegistryJsonRepository().load(registry_path)
    record = registry.records[0]
    output = capsys.readouterr().out
    assert result == 0
    assert record.confirmation_input.plan_id == "READY_PLAN"
    assert tuple(item.status.value for item in record.confirmation_input.prerequisites) == (
        "CONFIRMED", "UNKNOWN",
    )
    assert "Préparation enregistrée." in output
    assert "--channel-isolation-journey READY_PLAN" in output
    assert "--channel-isolation-preparation" in output
    assert "\n+  --" not in output
    assert "Aucune mesure ni expérience n’a été créée." in output
    assert "Causality status: NOT_ESTABLISHED" in output
    assert brain.calls[0]["return_context"] is True


def test_start_placement_decline_leaves_campaign_unchanged(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()

    result = acousticbrain_main.main(
        ("--measurements-root", str(root), "--start-placement"),
        brain=ContextBrain((ready_plan(),)),
        placement_input=answers("i", "i", "n"),
    )

    assert result == 0
    assert not (root / ".acousticbrain").exists()
    assert "Préparation non enregistrée" in capsys.readouterr().out


def test_start_placement_rejects_invalid_answer_without_writing(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            ("--measurements-root", str(root), "--start-placement"),
            brain=ContextBrain((ready_plan(),)),
            placement_input=answers("x"),
        )

    assert error.value.code == 2
    assert not (root / ".acousticbrain").exists()
    assert "Utilisez O, N ou I" in capsys.readouterr().err


def test_start_placement_is_exclusive_before_analysis(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    brain = ContextBrain((ready_plan(),))

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            (
                "--measurements-root", str(root), "--start-placement",
                "--full-assessment",
            ),
            brain=brain,
        )

    assert error.value.code == 2
    assert brain.calls == []
    assert "cannot be combined with --full-assessment" in capsys.readouterr().err


def test_start_placement_without_ready_plan_does_not_write(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()

    result = acousticbrain_main.main(
        ("--measurements-root", str(root), "--start-placement"),
        brain=ContextBrain(()),
    )

    assert result == 0
    assert not (root / ".acousticbrain").exists()
    assert "Aucune vérification de positionnement READY" in capsys.readouterr().out
