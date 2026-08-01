from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.application import evidence_acquisition_plan_fingerprint
from acousticbrain.models import (
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from acousticbrain.persistence import EvidencePlanPreparationRegistryJsonRepository
from acousticbrain.report import (
    EvidencePlanPreparationUserViewConsoleReporter,
    EvidencePlanPreparationUserViewPresenter,
)
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan


def registry_record(*statuses):
    return record(*statuses)


def registry_with(*statuses):
    return EvidencePlanPreparationRegistry().with_record(
        registry_record(*statuses)
    )


class ContextBrain:
    def __init__(self, plans):
        self.plans = plans
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return object(), SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(plans=self.plans)
        )


def test_view_preserves_unknown_and_all_recorded_decisions():
    registry = registry_with(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    view = EvidencePlanPreparationUserViewPresenter().present(
        registry, (ready_plan(),), "preparation-confirmation-001"
    )
    assert view.confirmation_id == "preparation-confirmation-001"
    assert view.plan_label == (
        "Plan d’acquisition de preuves — vérifier séparément les canaux"
    )
    assert view.prerequisite_lines == (
        "documented_microphone_position : CONFIRMED",
        "existing_acquisition_settings : UNKNOWN",
    )
    assert view.decision_lines == (
        "PLAN_EXACTLY_RESOLVED",
        "PREPARATION_DECLARED",
        "ALL_PREREQUISITES_USER_CONFIRMED : indisponible",
    )
    assert view.user_action_state == "REVIEW_UNKNOWN_PREREQUISITES"
    assert view.causality_status == "NOT_ESTABLISHED"


def test_not_confirmed_and_all_confirmed_have_distinct_single_actions():
    presenter = EvidencePlanPreparationUserViewPresenter()
    unconfirmed = presenter.present(
        registry_with(
            EvidencePlanPrerequisiteStatus.CONFIRMED,
            EvidencePlanPrerequisiteStatus.NOT_CONFIRMED,
        ),
        (ready_plan(),),
        "preparation-confirmation-001",
    )
    confirmed = presenter.present(
        registry_with(
            EvidencePlanPrerequisiteStatus.CONFIRMED,
            EvidencePlanPrerequisiteStatus.CONFIRMED,
        ),
        (ready_plan(),),
        "preparation-confirmation-001",
    )
    assert unconfirmed.user_action_state == "REVIEW_NOT_CONFIRMED_PREREQUISITES"
    assert confirmed.user_action_state == "NO_PREPARATION_STATUS_ACTION"
    assert confirmed.decision_lines[-1] == "ALL_PREREQUISITES_USER_CONFIRMED"


def test_unknown_confirmation_and_current_plan_fail_before_rendering():
    presenter = EvidencePlanPreparationUserViewPresenter()
    registry = registry_with(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    with pytest.raises(ValueError, match="Unknown.*confirmation_id"):
        presenter.present(registry, (ready_plan(),), "unknown")
    with pytest.raises(ValueError, match="plan unavailable"):
        presenter.present(registry, (), "preparation-confirmation-001")


def test_stale_current_plan_fingerprint_is_rejected():
    registry = registry_with(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    changed = replace(ready_plan(), objective="Changed after declaration")
    assert evidence_acquisition_plan_fingerprint(changed) != (
        registry.records[0].confirmation_input.plan_contract_fingerprint
    )
    with pytest.raises(ValueError, match="FINGERPRINT_MISMATCH"):
        EvidencePlanPreparationUserViewPresenter().present(
            registry, (changed,), "preparation-confirmation-001"
        )


def test_console_always_renders_four_blocks_and_boundary(capsys):
    view = EvidencePlanPreparationUserViewPresenter().present(
        registry_with(
            EvidencePlanPrerequisiteStatus.CONFIRMED,
            EvidencePlanPrerequisiteStatus.UNKNOWN,
        ),
        (ready_plan(),),
        "preparation-confirmation-001",
    )
    EvidencePlanPreparationUserViewConsoleReporter().print(view)
    output = capsys.readouterr().out
    assert "Préparation déclarée\n" in output
    assert "Statuts des prérequis\n" in output
    assert "Décisions enregistrées\n" in output
    assert "Action utilisateur\n" in output
    assert "Frontière scientifique\n" in output
    assert "Causality status: NOT_ESTABLISHED" in output


def test_cli_view_is_read_only_and_routes_exact_analysis_plans(tmp_path, capsys):
    registry_path = tmp_path / "preparations.json"
    registry = registry_with(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    repository = EvidencePlanPreparationRegistryJsonRepository()
    repository.save(registry_path, registry)
    before = registry_path.read_bytes()
    brain = ContextBrain((ready_plan(),))

    view = acousticbrain_main.view_evidence_plan_preparation(
        tmp_path,
        "preparation-confirmation-001",
        registry_path,
        brain=brain,
        registry_repository=repository,
    )

    assert view.confirmation_id == "preparation-confirmation-001"
    assert registry_path.read_bytes() == before
    assert brain.calls[0]["synthesize_evidence_acquisition"] is True
    assert "EVIDENCE PLAN PREPARATION VIEW" in capsys.readouterr().out


def test_parser_and_main_require_explicit_registry_and_dedicated_mode(
    tmp_path, capsys
):
    parsed = acousticbrain_main.create_parser().parse_args((
        "--evidence-plan-preparation-view", "confirmation-001",
        "--evidence-plan-preparation-registry", "state/preparations.json",
    ))
    assert parsed.evidence_plan_preparation_view == "confirmation-001"
    assert parsed.evidence_plan_preparation_registry == Path(
        "state/preparations.json"
    )
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--evidence-plan-preparation-view", "confirmation-001",
        ))
    assert "requires --evidence-plan-preparation-registry" in (
        capsys.readouterr().err
    )


def test_view_rejects_other_modes_before_analysis(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    brain = ContextBrain(())
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--evidence-plan-preparation-view", "confirmation-001",
            "--evidence-plan-preparation-registry", str(tmp_path / "registry.json"),
            "--full-assessment",
        ), brain=brain)
    assert brain.calls == []
    assert "cannot be combined with --full-assessment" in capsys.readouterr().err
