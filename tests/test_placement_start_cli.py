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
    assert "aucune expérience ne peut être déclarée" in output
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


def test_start_placement_guides_reference_and_test_name_before_declaration(
    tmp_path, capsys
):
    root = tmp_path / "measurements"
    root.mkdir()
    (root / "baseline-before-test").mkdir()

    result = acousticbrain_main.main(
        ("--measurements-root", str(root), "--start-placement"),
        brain=ContextBrain((ready_plan(),)),
        placement_input=answers("o", "o", "o", "1", "", "n"),
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "Choisissez la mesure de départ" in output
    assert "1. baseline-before-test" in output
    assert "Nouveau test : test-canaux-001" in output
    assert "Test non déclaré" in output
    assert not (root / "test-canaux-001").exists()
    assert not (root / "baseline-before-test" / "manifest.json").exists()


def test_start_placement_reuses_one_confirmed_preparation(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    (root / "baseline").mkdir()
    registry_path = root / acousticbrain_main.DEFAULT_PLACEMENT_PREPARATION_REGISTRY
    first = acousticbrain_main.main(
        ("--measurements-root", str(root), "--start-placement"),
        brain=ContextBrain((ready_plan(),)),
        placement_input=answers("o", "o", "o", "1", "", "n"),
    )
    before = registry_path.read_bytes()

    second = acousticbrain_main.main(
        ("--measurements-root", str(root), "--start-placement"),
        brain=ContextBrain((ready_plan(),)),
        placement_input=answers("1", "", "n"),
    )

    output = capsys.readouterr().out
    assert first == second == 0
    assert registry_path.read_bytes() == before
    assert "préparation de ce test est déjà enregistrée et confirmée" in output
    assert "Test non déclaré" in output


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
