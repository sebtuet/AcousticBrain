from dataclasses import replace

import pytest

from acousticbrain.application import EvidencePlanCompletionService
from acousticbrain.models import EvidenceAcquisitionStatus
from acousticbrain.persistence import EvidencePlanCompletionRegistryJsonRepository
from test_derived_evidence_plan import complete_protocol
from test_evidence_plan_completion_compatibility import protocol_action
from test_evidence_plan_completion_resolution import (
    blocking_factor,
    completion_input,
    protocol,
    source_plan,
)


def workflow_values(*, input_value=None, action=None):
    action = action or protocol_action()
    source = source_plan(
        corrective_action_id=action.action_id,
        reasoning_id="REASONING",
    )
    return {
        "completion_input": input_value or completion_input(),
        "source_plans": (source,),
        "blocking_factors": (blocking_factor(),),
        "actions": (action,),
        "protocol_references": (complete_protocol(),),
    }


def complete(service, path, **overrides):
    values = workflow_values(**overrides)
    input_value = values.pop("completion_input")
    return service.complete(input_value, registry_path=path, **values)


def test_service_persists_the_three_decisions_and_complete_provenance(tmp_path):
    path = tmp_path / "completion-registry.json"
    result = complete(EvidencePlanCompletionService(), path)

    assert result.persisted is True
    assert result.registry_path == str(path)
    assert result.record.resolution_status.value == "REFERENCE_RESOLVED"
    assert result.record.compatibility_status.value == "REFERENCE_COMPATIBLE"
    assert result.record.derived_plan.status.value == "DERIVED_PLAN_READY"
    assert result.record.derived_plan.source_plan.status is EvidenceAcquisitionStatus.BLOCKED
    assert result.record.derived_plan.plan.status is EvidenceAcquisitionStatus.READY
    assert EvidencePlanCompletionRegistryJsonRepository().load(path).records == (
        result.record,
    )


def test_identical_completion_is_idempotent_without_rewriting(tmp_path):
    path = tmp_path / "completion-registry.json"
    service = EvidencePlanCompletionService()
    first = complete(service, path)
    before = path.stat().st_mtime_ns
    second = complete(service, path)

    assert first.record == second.record
    assert second.persisted is False
    assert path.stat().st_mtime_ns == before


def test_divergent_reuse_fails_without_changing_the_registry(tmp_path):
    path = tmp_path / "completion-registry.json"
    service = EvidencePlanCompletionService()
    complete(service, path)
    before = path.read_bytes()
    changed = completion_input(declaration_source="other.json")

    with pytest.raises(ValueError, match="COMPLETION_INPUT_DIVERGENT"):
        complete(service, path, input_value=changed)

    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "mutation, error",
    (
        ("unknown_source", "SOURCE_PLAN_UNKNOWN"),
        ("incompatible", "REFERENCE_COMPATIBILITY_NOT_ESTABLISHED"),
        ("incomplete", "REFERENCE_CONTRACT_INCOMPLETE"),
    ),
)
def test_any_failed_decision_writes_nothing(tmp_path, mutation, error):
    path = tmp_path / "completion-registry.json"
    values = workflow_values()
    if mutation == "unknown_source":
        values["source_plans"] = ()
    elif mutation == "incompatible":
        values["actions"] = (replace(
            values["actions"][0], compatible_protocol_ids=()
        ),)
    else:
        values["protocol_references"] = (protocol(),)
    input_value = values.pop("completion_input")

    with pytest.raises(ValueError, match=error):
        EvidencePlanCompletionService().complete(
            input_value, registry_path=path, **values
        )

    assert not path.exists()


def test_second_completion_creates_a_distinct_unselected_candidate(tmp_path):
    path = tmp_path / "completion-registry.json"
    service = EvidencePlanCompletionService()
    first = complete(service, path)
    second = complete(
        service,
        path,
        input_value=completion_input(completion_input_id="completion-input-002"),
    )
    registry = EvidencePlanCompletionRegistryJsonRepository().load(path)

    assert second.persisted is True
    assert len(registry.records) == 2
    assert first.record.derived_plan.plan.plan_id != (
        second.record.derived_plan.plan.plan_id
    )


def test_completion_does_not_create_measurements_or_manifests(tmp_path):
    registry_path = tmp_path / "state" / "completion-registry.json"
    complete(EvidencePlanCompletionService(), registry_path)

    assert tuple(tmp_path.rglob("manifest.json")) == ()
    assert tuple(tmp_path.rglob("measurements")) == ()
    assert tuple(path for path in tmp_path.rglob("*") if path.is_file()) == (
        registry_path,
    )
