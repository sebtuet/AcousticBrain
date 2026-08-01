from dataclasses import replace
from types import SimpleNamespace

import pytest

from acousticbrain.application import (
    EvidenceAcquisitionPlanContractService,
    EvidenceAcquisitionPlanContractValidator,
    ExperimentDiscoveryService,
)
from acousticbrain.models import (
    EvidenceAcquisitionStatus,
    ExperimentContractMode,
    PlanCoverageStatus,
)
from acousticbrain.report import ExperimentDiscoveryPresenter
from acousticbrain.report import EvidenceAcquisitionPlanPresenter
from test_channel_isolation_plan_coverage import plan


def campaign(tmp_path):
    for name in ("baseline", "exp-001"):
        directory = tmp_path / name / "measurements"
        directory.mkdir(parents=True)
        (directory / "LEFT.txt").write_text(
            "Frequency SPL\n20 70\n", encoding="utf-8"
        )
    return tmp_path


def test_ready_plan_contract_round_trips_without_information_loss(tmp_path):
    root = campaign(tmp_path)
    source = plan()

    declared = EvidenceAcquisitionPlanContractService().declare(
        root, experiment_code="exp-001", reference_experiment_code="baseline",
        plan=source,
    )
    descriptor = next(
        item for item in ExperimentDiscoveryService().discover(root)
        if item.experiment_id == "exp-001"
    )

    assert declared.source_plan == source
    assert descriptor.source_evidence_acquisition_plan_id == source.plan_id
    assert descriptor.evidence_acquisition_plan_contract == declared
    assert descriptor.evidence_acquisition_plan_contract.source_plan == source
    assert descriptor.evidence_acquisition_plan_contract.mode is (
        ExperimentContractMode.EXPLORATORY
    )
    assert descriptor.experiment_declaration.reference_experiment_code == "baseline"
    assert descriptor.experiment_declaration.modified_variables == (
        "active_channel",
    )
    assert descriptor.experiment_declaration.controlled_variables == tuple(
        sorted(source.controlled_variables)
    )


def test_contract_validation_covers_every_semantic_plan_dimension(tmp_path):
    root = campaign(tmp_path)
    source = plan()
    contract = EvidenceAcquisitionPlanContractService().declare(
        root, experiment_code="exp-001", reference_experiment_code="baseline",
        plan=source,
    )

    result = EvidenceAcquisitionPlanContractValidator().validate(contract, source)

    assert result.status is PlanCoverageStatus.COMPLETE
    assert result.missing_requirements == ()
    assert set(result.covered_requirements) == {
        "plan_contract:identity", "plan_contract:objective",
        "plan_contract:variables", "plan_contract:measurements",
        "plan_contract:observations", "plan_contract:criteria",
        "plan_contract:limitations", "plan_contract:prerequisites",
        "plan_contract:provenance", "plan_contract:mode",
    }
    assert result.unverifiable_requirements == (
        "comparison_validity", "execution_conformance",
    )


def test_missing_or_changed_snapshot_is_never_reported_complete(tmp_path):
    source = plan()
    validator = EvidenceAcquisitionPlanContractValidator()
    missing = validator.validate(None, source)
    assert missing.status is PlanCoverageStatus.INSUFFICIENT_DECLARATION

    root = campaign(tmp_path)
    contract = EvidenceAcquisitionPlanContractService().declare(
        root, experiment_code="exp-001", reference_experiment_code="baseline",
        plan=source,
    )
    changed = replace(source, objective="A different objective.")
    mismatch = validator.validate(contract, changed)
    assert mismatch.status is PlanCoverageStatus.PARTIAL
    assert mismatch.missing_requirements == ("plan_contract:exact_source_match",)


def test_blocked_plan_and_prescriptive_mode_cannot_be_declared(tmp_path):
    root = campaign(tmp_path)
    service = EvidenceAcquisitionPlanContractService()
    with pytest.raises(ValueError, match="READY"):
        service.declare(
            root, experiment_code="exp-001", reference_experiment_code="baseline",
            plan=replace(plan(), status=EvidenceAcquisitionStatus.BLOCKED),
        )
    with pytest.raises(ValueError, match="future scientific contract"):
        service.declare(
            root, experiment_code="exp-001", reference_experiment_code="baseline",
            plan=plan(),
            mode=ExperimentContractMode.PRESCRIPTIVE,
        )


def test_existing_different_contract_reports_deterministic_incompatible_fields(tmp_path):
    root = campaign(tmp_path)
    service = EvidenceAcquisitionPlanContractService()
    service.declare(
        root, experiment_code="exp-001", reference_experiment_code="baseline",
        plan=plan(),
    )
    with pytest.raises(ValueError) as error:
        service.declare(
            root, experiment_code="exp-001", reference_experiment_code="baseline",
            plan=replace(plan(), objective="Changed objective."),
        )
    assert str(error.value) == (
        "Experiment already preserves a different plan contract; "
        "incompatible fields: plan.objective."
    )


def test_identical_contract_declaration_is_idempotent(tmp_path):
    root = campaign(tmp_path)
    service = EvidenceAcquisitionPlanContractService()
    arguments = dict(
        experiment_code="exp-001", reference_experiment_code="baseline",
        plan=plan(),
    )
    first = service.declare(root, **arguments)
    manifest = root / "exp-001/manifest.json"
    first_content = manifest.read_bytes()
    second = service.declare(root, **arguments)
    assert second == first
    assert manifest.read_bytes() == first_content


@pytest.mark.parametrize(
    ("changed", "expected_field"),
    (
        ({"reference_experiment_code": "alternate"}, "reference_experiment_code"),
        ({"user_note": "Different operator note."}, "declaration_user_note"),
    ),
)
def test_same_plan_cannot_reinterpret_experiment_declaration(
    tmp_path, changed, expected_field
):
    root = campaign(tmp_path)
    (root / "alternate").mkdir()
    service = EvidenceAcquisitionPlanContractService()
    initial = dict(
        experiment_code="exp-001", reference_experiment_code="baseline",
        plan=plan(), user_note=None,
    )
    service.declare(root, **initial)
    requested = {**initial, **changed}
    with pytest.raises(ValueError) as error:
        service.declare(root, **requested)
    assert f"incompatible fields: {expected_field}." in str(error.value)


def test_contract_declaration_does_not_modify_measurement_files(tmp_path):
    root = campaign(tmp_path)
    measurement = root / "exp-001/measurements/LEFT.txt"
    before = (measurement.read_bytes(), measurement.stat().st_mtime_ns)
    EvidenceAcquisitionPlanContractService().declare(
        root, experiment_code="exp-001", reference_experiment_code="baseline",
        plan=plan(),
    )
    assert (measurement.read_bytes(), measurement.stat().st_mtime_ns) == before


def test_discovery_report_exposes_contract_continuity_separately_from_execution(tmp_path):
    root = campaign(tmp_path)
    source = plan()
    EvidenceAcquisitionPlanContractService().declare(
        root, experiment_code="exp-001", reference_experiment_code="baseline",
        plan=source,
    )
    descriptors = ExperimentDiscoveryService().discover(root)
    presented = ExperimentDiscoveryPresenter().present(SimpleNamespace(
        experiment_descriptors=descriptors,
        evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(source,)),
    ))
    experiment = next(
        item for item in presented.experiments if item.experiment_id == "exp-001"
    )
    assert experiment.plan_contract_preservation_status == "PLAN_COVERAGE_COMPLETE"
    assert "plan_contract:objective" in experiment.preserved_plan_contract_fields
    assert experiment.unverifiable_plan_contract_fields == (
        "comparison_validity", "execution_conformance",
    )


def test_explicit_command_resolves_ready_plan_and_preserves_exact_contract(tmp_path):
    from acousticbrain.commands import declare_evidence_plan_experiment as command

    root = campaign(tmp_path)
    source = plan()
    presented = EvidenceAcquisitionPlanPresenter().present(SimpleNamespace(
        evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(source,)),
    ))
    report = SimpleNamespace(evidence_acquisition_plans=presented)
    brain = SimpleNamespace(analyze=lambda **arguments: report)

    command.main([
        str(root), "--plan-id", source.plan_id,
        "--experiment", "exp-001", "--reference", "baseline",
    ], brain=brain)

    descriptor = next(
        item for item in ExperimentDiscoveryService().discover(root)
        if item.experiment_id == "exp-001"
    )
    assert descriptor.evidence_acquisition_plan_contract.source_plan == source


def test_explicit_command_resolves_derived_plan_from_completion_registry(tmp_path):
    from acousticbrain.commands import declare_evidence_plan_experiment as command
    from acousticbrain.models import EvidencePlanCompletionRegistry
    from acousticbrain.persistence import EvidencePlanCompletionRegistryJsonRepository
    from test_evidence_plan_completion_registry import record

    root = campaign(tmp_path)
    completion = record()
    registry_path = tmp_path / "completion-registry.json"
    EvidencePlanCompletionRegistryJsonRepository().save(
        registry_path,
        EvidencePlanCompletionRegistry().with_record(completion),
    )
    report = SimpleNamespace(
        evidence_acquisition_plans=SimpleNamespace(plans=())
    )
    brain = SimpleNamespace(analyze=lambda **arguments: report)

    command.main([
        str(root),
        "--completion-registry", str(registry_path),
        "--plan-id", completion.derived_plan.plan.plan_id,
        "--experiment", "exp-derived",
        "--reference", "baseline",
    ], brain=brain)

    from acousticbrain.persistence import (
        EvidenceAcquisitionPlanContractJsonCodec,
        MeasurementRepository,
    )

    manifest = MeasurementRepository.load_manifest(root / "exp-derived")
    contract = EvidenceAcquisitionPlanContractJsonCodec().loads(
        manifest["evidence_acquisition_plan_contract"]
    )
    assert contract.source_plan == completion.derived_plan.plan
    assert contract.declaration_source == (
        "RESOLVED_DERIVED_EVIDENCE_ACQUISITION_PLAN:"
        + completion.completion_input.completion_input_id
    )
    assert completion.derived_plan.source_plan.status.value == "BLOCKED"


def test_derived_plan_ambiguity_fails_before_creating_experiment_directory(tmp_path):
    from acousticbrain.commands import declare_evidence_plan_experiment as command
    from acousticbrain.models import EvidencePlanCompletionRegistry
    from acousticbrain.persistence import EvidencePlanCompletionRegistryJsonRepository
    from acousticbrain.report import EvidenceAcquisitionPlanPresenter
    from test_evidence_plan_completion_registry import record

    root = campaign(tmp_path)
    completion = record()
    registry_path = tmp_path / "completion-registry.json"
    EvidencePlanCompletionRegistryJsonRepository().save(
        registry_path,
        EvidencePlanCompletionRegistry().with_record(completion),
    )
    presented = EvidenceAcquisitionPlanPresenter().present(SimpleNamespace(
        evidence_acquisition_plan_synthesis=SimpleNamespace(
            plans=(completion.derived_plan.plan,)
        ),
    ))
    brain = SimpleNamespace(analyze=lambda **arguments: SimpleNamespace(
        evidence_acquisition_plans=presented
    ))

    with pytest.raises(ValueError, match="not uniquely READY"):
        command.main([
            str(root),
            "--completion-registry", str(registry_path),
            "--plan-id", completion.derived_plan.plan.plan_id,
            "--experiment", "exp-ambiguous",
            "--reference", "baseline",
        ], brain=brain)

    assert not (root / "exp-ambiguous").exists()


def test_unknown_derived_plan_fails_without_creating_experiment_directory(tmp_path):
    from acousticbrain.commands import declare_evidence_plan_experiment as command

    root = campaign(tmp_path)
    brain = SimpleNamespace(analyze=lambda **arguments: SimpleNamespace(
        evidence_acquisition_plans=SimpleNamespace(plans=())
    ))

    with pytest.raises(ValueError, match="not uniquely READY"):
        command.main([
            str(root),
            "--plan-id", "DERIVED_UNKNOWN",
            "--experiment", "exp-unknown",
            "--reference", "baseline",
        ], brain=brain)

    assert not (root / "exp-unknown").exists()
