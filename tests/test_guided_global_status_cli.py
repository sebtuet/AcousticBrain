from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.application import ChannelIsolationOperationalWorksheetService
from acousticbrain.models import (
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan
from test_guided_global_status_presenter import declared_experiment_view, report_for
from acousticbrain.report import PresentedExperimentUserView


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


class DeclaredExperimentPresenter:
    def __init__(self, view):
        self.view = view
        self.calls = []

    def present(self, report, experiment_id):
        self.calls.append((report, experiment_id))
        return self.view


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


def test_cli_projects_explicit_incomplete_operational_records_without_writing(
    tmp_path, capsys
):
    plan = ready_plan()
    worksheets = ChannelIsolationOperationalWorksheetService().generate(
        plan.plan_id, plans=(plan,)
    )
    microphone_path = tmp_path / "microphone.json"
    settings_path = tmp_path / "settings.json"
    registry_path = tmp_path / "preparations.json"
    microphone_path.write_text(
        acousticbrain_main.json.dumps(worksheets.microphone_position),
        encoding="utf-8",
    )
    settings_path.write_text(
        acousticbrain_main.json.dumps(worksheets.acquisition_settings),
        encoding="utf-8",
    )
    registry_path.write_text("preserve\n", encoding="utf-8")
    confirmation = record(
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    repository = Repository(
        EvidencePlanPreparationRegistry().with_record(confirmation)
    )
    before = {
        path.name: path.read_bytes() for path in tmp_path.iterdir()
    }
    result = acousticbrain_main.show_guided_status(
        tmp_path,
        registry_path,
        confirmation.confirmation_input.confirmation_id,
        brain=Brain(),
        registry_repository=repository,
        microphone_position_path=microphone_path,
        acquisition_settings_path=settings_path,
    )
    output = capsys.readouterr().out
    assert result.workflow_state == (
        "READY_PLAN_OPERATIONAL_DOCUMENTATION_INCOMPLETE"
    )
    assert "microphone_position.reference_geometry" in output
    assert "documented_microphone_position=UNKNOWN" in output
    assert {
        path.name: path.read_bytes() for path in tmp_path.iterdir()
    } == before


def test_cli_projects_exact_declaration_readiness_without_creating_target(
    tmp_path, capsys
):
    (tmp_path / "baseline").mkdir()
    registry_path = tmp_path / "preparations.json"
    registry_path.write_text("preserve\n", encoding="utf-8")
    confirmation = record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    repository = Repository(
        EvidencePlanPreparationRegistry().with_record(confirmation)
    )
    before = {
        path.name: path.read_bytes() if path.is_file() else None
        for path in tmp_path.iterdir()
    }
    result = acousticbrain_main.show_guided_status(
        tmp_path,
        registry_path,
        confirmation.confirmation_input.confirmation_id,
        brain=Brain(),
        registry_repository=repository,
        reference_experiment_id="baseline",
        experiment_id="channel-isolation-001",
    )
    output = capsys.readouterr().out
    assert result.workflow_state == "READY_PLAN_DECLARATION_READY"
    assert output.count("Action utilisateur") == 1
    assert "--experiment channel-isolation-001" in output
    assert "--reference baseline" in output
    assert "--preparation-registry" in output
    assert (
        "--preparation " + confirmation.confirmation_input.confirmation_id
        in output
    )
    assert not (tmp_path / "channel-isolation-001").exists()
    assert {
        path.name: path.read_bytes() if path.is_file() else None
        for path in tmp_path.iterdir()
    } == before


def test_cli_projects_explicit_declared_experiment_without_writing(tmp_path, capsys):
    registry_path = tmp_path / "preparations.json"
    registry_path.write_text("preserve\n", encoding="utf-8")
    confirmation = record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    repository = Repository(
        EvidencePlanPreparationRegistry().with_record(confirmation)
    )
    plan = ready_plan()
    view = PresentedExperimentUserView(
        experiment_id="exp-008",
        lifecycle_state="ACQUISITION_PENDING",
        intent_lines=(plan.objective,),
        user_action_state="COMPLETE_REQUIRED_ACQUISITION",
        user_action="Compléter l’acquisition requise déjà déclarée.",
        observed_result="NOT_AVAILABLE",
        observed_result_lines=("Aucune comparaison locale unique n’est disponible.",),
        scientific_boundary_lines=("Comparaison locale indisponible.",),
        causality_status="NOT_ESTABLISHED",
        source_plan_id=plan.plan_id,
        preparation_confirmation_id=confirmation.confirmation_input.confirmation_id,
        preparation_plan_fingerprint=(
            confirmation.confirmation_input.plan_contract_fingerprint
        ),
        preparation_qualification_status="ALL_PREREQUISITES_USER_CONFIRMED",
        declared_plan_coverage_status="PLAN_COVERAGE_PARTIAL",
    )
    experiment_presenter = DeclaredExperimentPresenter(view)
    before = registry_path.read_bytes()
    result = acousticbrain_main.show_guided_status(
        tmp_path,
        registry_path,
        confirmation.confirmation_input.confirmation_id,
        brain=Brain(),
        registry_repository=repository,
        declared_experiment_id="exp-008",
        declared_experiment_view_presenter=experiment_presenter,
    )
    output = capsys.readouterr().out
    assert result.workflow_state == (
        "READY_PLAN_EXPERIMENT_DECLARED_ACQUISITION_PENDING"
    )
    assert "Expérience déclarée : exp-008" in output
    assert output.count("Action utilisateur") == 1
    assert experiment_presenter.calls[0][1] == "exp-008"
    assert registry_path.read_bytes() == before


def test_cli_projects_complete_acquisition_waiting_for_comparison_without_writing(
    tmp_path, capsys
):
    registry_path = tmp_path / "preparations.json"
    registry_path.write_text("preserve\n", encoding="utf-8")
    confirmation = record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    repository = Repository(
        EvidencePlanPreparationRegistry().with_record(confirmation)
    )
    plan = ready_plan()
    view = declared_experiment_view(
        plan,
        confirmation.confirmation_input.confirmation_id,
        confirmation.confirmation_input.plan_contract_fingerprint,
        "COMPARISON_UNAVAILABLE",
    )
    experiment_presenter = DeclaredExperimentPresenter(view)
    before = registry_path.read_bytes()
    result = acousticbrain_main.show_guided_status(
        tmp_path,
        registry_path,
        confirmation.confirmation_input.confirmation_id,
        brain=Brain(),
        registry_repository=repository,
        declared_experiment_id="exp-008",
        declared_experiment_view_presenter=experiment_presenter,
    )
    output = capsys.readouterr().out
    assert result.workflow_state == (
        "READY_PLAN_EXPERIMENT_ACQUISITION_COMPLETE_COMPARISON_UNAVAILABLE"
    )
    assert "Acquisition spécialisée complète" in output
    assert "Rétablir la comparabilité" in output
    assert output.count("Action utilisateur") == 1
    assert "Causality status: NOT_ESTABLISHED" in output
    assert registry_path.read_bytes() == before


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


def test_main_requires_exact_preparation_for_guided_operational_records(
    tmp_path, capsys
):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--guided-status",
            "--microphone-position-record", str(tmp_path / "microphone.json"),
            "--acquisition-settings-record", str(tmp_path / "settings.json"),
        ))
    assert "requires --guided-preparation-registry and --guided-preparation" in (
        capsys.readouterr().err
    )


def test_main_requires_both_guided_operational_record_paths(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--guided-status",
            "--guided-preparation-registry", str(tmp_path / "registry.json"),
            "--guided-preparation", "preparation-001",
            "--microphone-position-record", str(tmp_path / "microphone.json"),
        ))
    assert "requires both --microphone-position-record" in capsys.readouterr().err


def test_main_requires_both_guided_declaration_identifiers(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--guided-status",
            "--guided-preparation-registry", str(tmp_path / "registry.json"),
            "--guided-preparation", "preparation-001",
            "--channel-isolation-reference", "baseline",
        ))
    assert "requires both --channel-isolation-reference" in (
        capsys.readouterr().err
    )


def test_main_requires_exact_preparation_for_guided_declaration(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--guided-status",
            "--channel-isolation-reference", "baseline",
            "--channel-isolation-experiment", "channel-isolation-001",
        ))
    assert "requires --guided-preparation-registry and --guided-preparation" in (
        capsys.readouterr().err
    )


def test_main_requires_guided_mode_for_declared_experiment(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--guided-declared-experiment", "exp-008",
        ))
    assert "requires --guided-status" in capsys.readouterr().err


def test_main_requires_exact_preparation_for_declared_experiment(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--guided-status",
            "--guided-declared-experiment", "exp-008",
        ))
    assert "requires --guided-preparation-registry and --guided-preparation" in (
        capsys.readouterr().err
    )


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
