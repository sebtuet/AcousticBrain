from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.commands import declare_evidence_plan_experiment
from acousticbrain.models import (
    EvidencePlanCompletionRegistry,
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from acousticbrain.persistence import (
    EvidencePlanCompletionRegistryJsonRepository,
    EvidencePlanPreparationRegistryJsonRepository,
    MeasurementRepository,
)
from acousticbrain.report import EvidenceAcquisitionPlanPresenter
from test_channel_isolation_plan_coverage import plan
from test_evidence_acquisition_plan_contract import campaign
from test_evidence_plan_completion_registry import record as completion_record
from test_evidence_plan_preparation_registry import record as preparation_record
from test_evidence_plan_preparation_resolution import ready_plan


class Brain:
    def __init__(self, plans):
        self.report = SimpleNamespace(
            evidence_acquisition_plans=EvidenceAcquisitionPlanPresenter().present(
                SimpleNamespace(
                    evidence_acquisition_plan_synthesis=SimpleNamespace(plans=plans)
                )
            )
        )
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return self.report


def declaration_arguments(root, source, experiment="exp-001"):
    return (
        "--measurements-root", str(root),
        "--declare-evidence-plan-experiment", experiment,
        "--evidence-plan-id", source.plan_id,
        "--evidence-plan-reference", "baseline",
    )


def test_parser_accepts_public_evidence_plan_declaration_options():
    arguments = acousticbrain_main.create_parser().parse_args((
        "--declare-evidence-plan-experiment", "exp-001",
        "--evidence-plan-id", "PLAN",
        "--evidence-plan-reference", "baseline",
        "--evidence-plan-declaration-note", "Exact note",
        "--evidence-plan-declaration-preparation-registry", "preparations.json",
        "--evidence-plan-declaration-preparation", "preparation-001",
    ))

    assert arguments.declare_evidence_plan_experiment == "exp-001"
    assert arguments.evidence_plan_id == "PLAN"
    assert arguments.evidence_plan_reference == "baseline"
    assert arguments.evidence_plan_declaration_note == "Exact note"
    assert str(arguments.evidence_plan_declaration_preparation_registry) == (
        "preparations.json"
    )
    assert arguments.evidence_plan_declaration_preparation == "preparation-001"


def test_main_requires_public_declaration_arguments_and_paired_preparation(
    tmp_path,
    capsys,
):
    root = campaign(tmp_path)
    source = plan()
    brain = Brain((source,))

    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--declare-evidence-plan-experiment", "exp-missing",
        ), brain=brain)
    assert "--evidence-plan-id, --evidence-plan-reference" in (
        capsys.readouterr().err
    )
    assert not (root / "exp-missing").exists()

    with pytest.raises(SystemExit):
        acousticbrain_main.main(
            declaration_arguments(root, source, "exp-unpaired") + (
                "--evidence-plan-declaration-preparation", "preparation-001",
            ),
            brain=brain,
        )
    assert "requires both" in capsys.readouterr().err
    assert not (root / "exp-unpaired").exists()

    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--evidence-plan-id", source.plan_id,
        ), brain=brain)
    assert "require --declare-evidence-plan-experiment" in capsys.readouterr().err

    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--record-exploratory-feasibility", "FEASIBLE",
            "--evidence-plan-id", source.plan_id,
        ), brain=brain)
    assert "cannot be combined with evidence-plan declaration options" in (
        capsys.readouterr().err
    )


def test_main_rejects_an_incompatible_mode_before_declaration(tmp_path, capsys):
    root = campaign(tmp_path)
    source = plan()
    brain = Brain((source,))

    with pytest.raises(SystemExit):
        acousticbrain_main.main(
            declaration_arguments(root, source, "exp-conflict") + (
                "--full-assessment",
            ),
            brain=brain,
        )

    assert "cannot be combined with --full-assessment" in capsys.readouterr().err
    assert brain.calls == []
    assert not (root / "exp-conflict").exists()


def test_main_declares_a_current_ready_plan_idempotently_without_measurements(
    tmp_path,
    capsys,
):
    root = campaign(tmp_path)
    source = plan()
    brain = Brain((source,))
    measurement = root / "exp-001" / "measurements" / "LEFT.txt"
    before_measurement = (measurement.read_bytes(), measurement.stat().st_mtime_ns)
    arguments = declaration_arguments(root, source)

    assert acousticbrain_main.main(arguments, brain=brain) == 0
    manifest = root / "exp-001" / "manifest.json"
    first = manifest.read_bytes()
    assert acousticbrain_main.main(arguments, brain=brain) == 0

    output = capsys.readouterr().out
    assert "Declared exp-001 from evidence-acquisition plan PLAN" in output
    assert manifest.read_bytes() == first
    assert (measurement.read_bytes(), measurement.stat().st_mtime_ns) == (
        before_measurement
    )
    persisted = MeasurementRepository.load_manifest(root / "exp-001")
    assert "evidence_acquisition_plan_contract" in persisted
    assert "causal_protocol_step" not in persisted
    assert "recommendation" not in persisted


def test_main_declaration_has_exact_manifest_parity_with_internal_command(
    tmp_path,
):
    source = plan()
    main_root = campaign(tmp_path / "main")
    internal_root = campaign(tmp_path / "internal")

    assert acousticbrain_main.main(
        declaration_arguments(main_root, source),
        brain=Brain((source,)),
    ) == 0
    declare_evidence_plan_experiment.main((
        str(internal_root),
        "--plan-id", source.plan_id,
        "--experiment", "exp-001",
        "--reference", "baseline",
    ), brain=Brain((source,)))

    assert (main_root / "exp-001" / "manifest.json").read_bytes() == (
        internal_root / "exp-001" / "manifest.json"
    ).read_bytes()


def test_main_declares_a_derived_plan_from_the_existing_completion_registry(
    tmp_path,
):
    root = campaign(tmp_path)
    completion = completion_record()
    registry_path = tmp_path / "completion-registry.json"
    EvidencePlanCompletionRegistryJsonRepository().save(
        registry_path,
        EvidencePlanCompletionRegistry().with_record(completion),
    )

    assert acousticbrain_main.main((
        "--measurements-root", str(root),
        "--declare-evidence-plan-experiment", "exp-derived",
        "--evidence-plan-id", completion.derived_plan.plan.plan_id,
        "--evidence-plan-reference", "baseline",
        "--evidence-plan-completion-registry", str(registry_path),
    ), brain=Brain(())) == 0

    manifest = MeasurementRepository.load_manifest(root / "exp-derived")
    assert manifest["evidence_acquisition_plan_contract"]["declaration_source"] == (
        "RESOLVED_DERIVED_EVIDENCE_ACQUISITION_PLAN:"
        + completion.completion_input.completion_input_id
    )


def test_main_declares_a_qualified_channel_isolation_plan_and_rejects_failed_preflight(
    tmp_path,
    capsys,
):
    root = campaign(tmp_path)
    source = ready_plan()
    confirmation = preparation_record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    registry_path = tmp_path / "preparations.json"
    EvidencePlanPreparationRegistryJsonRepository().save(
        registry_path,
        EvidencePlanPreparationRegistry().with_record(confirmation),
    )
    arguments = declaration_arguments(root, source, "exp-qualified") + (
        "--evidence-plan-declaration-preparation-registry", str(registry_path),
        "--evidence-plan-declaration-preparation",
        confirmation.confirmation_input.confirmation_id,
    )

    assert acousticbrain_main.main(arguments, brain=Brain((source,))) == 0
    manifest = MeasurementRepository.load_manifest(root / "exp-qualified")
    assert manifest["channel_isolation_preparation"]["confirmation_id"] == (
        confirmation.confirmation_input.confirmation_id
    )
    assert not (root / "exp-qualified" / "measurements").exists()

    incomplete = preparation_record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    incomplete_path = tmp_path / "incomplete-preparations.json"
    EvidencePlanPreparationRegistryJsonRepository().save(
        incomplete_path,
        EvidencePlanPreparationRegistry().with_record(incomplete),
    )
    with pytest.raises(SystemExit):
        acousticbrain_main.main(
            declaration_arguments(root, source, "exp-blocked") + (
                "--evidence-plan-declaration-preparation-registry",
                str(incomplete_path),
                "--evidence-plan-declaration-preparation",
                incomplete.confirmation_input.confirmation_id,
            ),
            brain=Brain((source,)),
        )
    assert "PREPARATION_INCOMPLETE" in capsys.readouterr().err
    assert not (root / "exp-blocked").exists()
