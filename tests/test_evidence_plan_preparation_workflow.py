from dataclasses import replace

import pytest

from acousticbrain.application import (
    EvidencePlanPreparationWorkflowService,
    evidence_acquisition_plan_fingerprint,
)
from acousticbrain.models import EvidencePlanPrerequisiteStatus
from acousticbrain.persistence import (
    EvidencePlanPreparationRegistryJsonRepository,
)
from test_evidence_plan_preparation_resolution import confirmation, ready_plan


def workflow_values(*, confirmation_id="preparation-confirmation-001"):
    plan = ready_plan()
    return plan, confirmation(
        plan,
        confirmation_id=confirmation_id,
        prerequisites=tuple(
            replace(value, status=status)
            for value, status in zip(
                confirmation(plan).prerequisites,
                (
                    EvidencePlanPrerequisiteStatus.CONFIRMED,
                    EvidencePlanPrerequisiteStatus.UNKNOWN,
                ),
            )
        ),
    )


def test_workflow_persists_exact_resolution_and_separate_decisions(tmp_path):
    path = tmp_path / "preparation-registry.json"
    plan, input_value = workflow_values()

    result = EvidencePlanPreparationWorkflowService().record(
        input_value, registry_path=path, plans=(plan,)
    )

    assert result.persisted is True
    assert result.registry_path == str(path)
    assert result.record.resolution_status.value == "PLAN_EXACTLY_RESOLVED"
    assert result.record.declaration_status.value == "PREPARATION_DECLARED"
    assert result.record.all_prerequisites_status is None
    assert EvidencePlanPreparationRegistryJsonRepository().load(path).records == (
        result.record,
    )


def test_identical_workflow_is_idempotent_without_rewriting(tmp_path):
    path = tmp_path / "preparation-registry.json"
    plan, input_value = workflow_values()
    service = EvidencePlanPreparationWorkflowService()
    first = service.record(input_value, registry_path=path, plans=(plan,))
    before = path.stat().st_mtime_ns
    second = service.record(input_value, registry_path=path, plans=(plan,))
    assert first.record == second.record
    assert second.persisted is False
    assert path.stat().st_mtime_ns == before


def test_divergent_reuse_fails_without_changing_registry(tmp_path):
    path = tmp_path / "preparation-registry.json"
    plan, input_value = workflow_values()
    service = EvidencePlanPreparationWorkflowService()
    service.record(input_value, registry_path=path, plans=(plan,))
    before = path.read_bytes()

    with pytest.raises(ValueError, match="PREPARATION_CONFIRMATION_DIVERGENT"):
        service.record(
            replace(input_value, declaration_source="SECOND_USER_JSON"),
            registry_path=path,
            plans=(plan,),
        )

    assert path.read_bytes() == before


@pytest.mark.parametrize(
    ("mutation", "error"),
    (
        ("unknown", "PREPARATION_PLAN_UNKNOWN"),
        ("stale", "PLAN_CONTRACT_FINGERPRINT_MISMATCH"),
    ),
)
def test_failed_resolution_writes_nothing(tmp_path, mutation, error):
    path = tmp_path / "preparation-registry.json"
    plan, input_value = workflow_values()
    plans = () if mutation == "unknown" else (plan,)
    if mutation == "stale":
        input_value = replace(input_value, plan_contract_fingerprint="a" * 64)
        assert input_value.plan_contract_fingerprint != (
            evidence_acquisition_plan_fingerprint(plan)
        )
    with pytest.raises(ValueError, match=error):
        EvidencePlanPreparationWorkflowService().record(
            input_value, registry_path=path, plans=plans
        )
    assert not path.exists()


def test_second_confirmation_for_same_plan_remains_distinct(tmp_path):
    path = tmp_path / "preparation-registry.json"
    plan, first_input = workflow_values()
    _, second_input = workflow_values(confirmation_id="preparation-confirmation-002")
    service = EvidencePlanPreparationWorkflowService()
    service.record(first_input, registry_path=path, plans=(plan,))
    service.record(second_input, registry_path=path, plans=(plan,))
    records = EvidencePlanPreparationRegistryJsonRepository().load(path).records
    assert len(records) == 2
    assert tuple(value.confirmation_input.confirmation_id for value in records) == (
        "preparation-confirmation-001",
        "preparation-confirmation-002",
    )


def test_workflow_creates_only_the_explicit_registry(tmp_path):
    path = tmp_path / "state" / "preparation-registry.json"
    plan, input_value = workflow_values()
    EvidencePlanPreparationWorkflowService().record(
        input_value, registry_path=path, plans=(plan,)
    )
    assert tuple(item for item in tmp_path.rglob("*") if item.is_file()) == (path,)
    assert tuple(tmp_path.rglob("manifest.json")) == ()
