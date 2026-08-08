import pytest

from acousticbrain.application import ChannelIsolationDeclarationReadinessService
from acousticbrain.models import (
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan


def registry(left, right):
    return EvidencePlanPreparationRegistry().with_record(record(left, right))


def qualify(tmp_path, preparation_registry, **changes):
    plan = ready_plan()
    values = {
        "measurement_root": tmp_path,
        "plan_id": plan.plan_id,
        "confirmation_id": preparation_registry.records[0].confirmation_input.confirmation_id,
        "reference_experiment_id": "baseline",
        "experiment_id": "channel-isolation-001",
        "plans": (plan,),
        "registry": preparation_registry,
    }
    values.update(changes)
    return ChannelIsolationDeclarationReadinessService().qualify(
        values.pop("measurement_root"),
        values.pop("plan_id"),
        values.pop("confirmation_id"),
        values.pop("reference_experiment_id"),
        values.pop("experiment_id"),
        **values,
    )


def test_all_confirmed_preflight_is_read_only_and_uses_closed_statuses(tmp_path):
    preparation_registry = registry(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    (tmp_path / "baseline").mkdir()
    before = tuple(path.name for path in tmp_path.iterdir())
    result = qualify(tmp_path, preparation_registry)
    assert result.statuses == (
        "PLAN_EXACTLY_RESOLVED",
        "PREPARATION_EXACTLY_RESOLVED",
        "ALL_PREREQUISITES_USER_CONFIRMED",
        "REFERENCE_EXACTLY_RESOLVED",
        "EXPERIMENT_TARGET_AVAILABLE",
        "DECLARATION_READY",
    )
    assert result.user_action_state == "DECLARE_EXPERIMENT_SEPARATELY"
    assert tuple(path.name for path in tmp_path.iterdir()) == before
    assert not (tmp_path / result.experiment_id).exists()


def test_incomplete_preparation_is_rejected(tmp_path):
    preparation_registry = registry(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    with pytest.raises(ValueError, match="PREPARATION_INCOMPLETE"):
        qualify(tmp_path, preparation_registry)


@pytest.mark.parametrize(
    ("changes", "message"),
    (
        ({"reference_experiment_id": "missing"}, "REFERENCE_UNKNOWN"),
        ({"experiment_id": "baseline"}, "must differ"),
        ({"experiment_id": "../escape"}, "exact safe text"),
    ),
)
def test_reference_and_target_identifiers_are_strict(tmp_path, changes, message):
    preparation_registry = registry(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    if changes.get("reference_experiment_id", "baseline") == "baseline":
        (tmp_path / "baseline").mkdir()
    with pytest.raises(ValueError, match=message):
        qualify(tmp_path, preparation_registry, **changes)


def test_existing_target_is_rejected_without_mutation(tmp_path):
    preparation_registry = registry(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    target = tmp_path / "channel-isolation-001"
    target.mkdir()
    (tmp_path / "baseline").mkdir()
    before = tuple(sorted(path.name for path in tmp_path.iterdir()))
    with pytest.raises(ValueError, match="TARGET_EXISTS"):
        qualify(tmp_path, preparation_registry)
    assert tuple(sorted(path.name for path in tmp_path.iterdir())) == before
