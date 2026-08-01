import json
from dataclasses import replace

import pytest

from acousticbrain.application import DerivedEvidenceAcquisitionPlanFactory
from acousticbrain.models import (
    EvidenceAcquisitionStatus,
    EvidencePlanCompletionCompatibilityStatus,
    EvidencePlanCompletionRecord,
    EvidencePlanCompletionRegistry,
    EvidencePlanCompletionResolutionStatus,
)
from acousticbrain.persistence import (
    EvidencePlanCompletionRegistryJsonCodec,
    EvidencePlanCompletionRegistryJsonRepository,
)
from test_derived_evidence_plan import protocol_compatibility
from test_evidence_plan_completion_resolution import completion_input


def record(*, completion_input_id="completion-input-001"):
    compatibility = protocol_compatibility(input_value=completion_input(
        completion_input_id=completion_input_id,
    ))
    return EvidencePlanCompletionRecord(
        completion_input=compatibility.resolution.completion_input,
        resolution_status=EvidencePlanCompletionResolutionStatus.REFERENCE_RESOLVED,
        compatibility_status=(
            EvidencePlanCompletionCompatibilityStatus.REFERENCE_COMPATIBLE
        ),
        derived_plan=DerivedEvidenceAcquisitionPlanFactory().create(compatibility),
    )


def test_registry_round_trip_preserves_the_complete_derivation():
    registry = EvidencePlanCompletionRegistry().with_record(record())
    codec = EvidencePlanCompletionRegistryJsonCodec()

    restored = codec.loads(codec.dumps(registry))

    assert restored == registry
    assert restored.records[0].derived_plan.source_plan.status is (
        EvidenceAcquisitionStatus.BLOCKED
    )
    assert restored.records[0].derived_plan.plan.status is EvidenceAcquisitionStatus.READY


def test_missing_registry_is_empty_and_save_is_atomic_and_idempotent(tmp_path):
    path = tmp_path / "state" / "evidence-plan-completions.json"
    repository = EvidencePlanCompletionRegistryJsonRepository()
    registry = EvidencePlanCompletionRegistry().with_record(record())
    assert repository.load(path) == EvidencePlanCompletionRegistry()

    assert repository.save(path, registry) is True
    first = path.read_bytes()
    first_mtime = path.stat().st_mtime_ns
    assert repository.save(path, registry) is False

    assert path.read_bytes() == first
    assert path.stat().st_mtime_ns == first_mtime
    assert not path.with_suffix(".json.tmp").exists()
    assert repository.load(path) == registry


def test_identical_recording_is_an_idempotent_registry_operation():
    first = record()
    registry = EvidencePlanCompletionRegistry().with_record(first)
    assert registry.with_record(record()) is registry


def test_divergent_completion_id_reports_sorted_incompatible_fields():
    first = record()
    divergent = replace(
        first,
        completion_input=replace(
            first.completion_input,
            declaration_source="other.json",
            user_note="Different intent",
        ),
    )
    with pytest.raises(ValueError) as caught:
        EvidencePlanCompletionRegistry().with_record(first).with_record(divergent)
    assert str(caught.value) == (
        "COMPLETION_INPUT_DIVERGENT: incompatible fields: "
        "completion_input.declaration_source, completion_input.user_note"
    )


def test_derived_identity_collision_is_never_selected_implicitly():
    first = record()
    second = record(completion_input_id="completion-input-002")
    collision = replace(
        second,
        derived_plan=replace(
            second.derived_plan,
            plan=replace(
                second.derived_plan.plan,
                plan_id=first.derived_plan.plan.plan_id,
            ),
        ),
    )
    with pytest.raises(ValueError, match="DERIVED_IDENTITY_AMBIGUOUS"):
        EvidencePlanCompletionRegistry().with_record(first).with_record(collision)


@pytest.mark.parametrize(
    "mutation, message",
    (
        (lambda value: value.update(schema_version=99), "Unsupported"),
        (lambda value: value.update(unknown=True), "Unknown registry fields"),
        (lambda value: value.pop("records"), "Missing registry fields"),
    ),
)
def test_registry_json_rejects_invalid_contracts(mutation, message):
    payload = json.loads(EvidencePlanCompletionRegistryJsonCodec().dumps(
        EvidencePlanCompletionRegistry()
    ))
    mutation(payload)
    with pytest.raises(ValueError, match=message):
        EvidencePlanCompletionRegistryJsonCodec().loads(json.dumps(payload))


def test_validation_failure_preserves_existing_registry_file(tmp_path):
    path = tmp_path / "evidence-plan-completions.json"
    path.write_text("preserve", encoding="utf-8")
    with pytest.raises(TypeError):
        EvidencePlanCompletionRegistryJsonRepository().save(path, object())
    assert path.read_text(encoding="utf-8") == "preserve"


def test_serialization_order_is_deterministic():
    first = record(completion_input_id="completion-input-001")
    second = record(completion_input_id="completion-input-002")
    left = EvidencePlanCompletionRegistry().with_record(second).with_record(first)
    right = EvidencePlanCompletionRegistry().with_record(first).with_record(second)
    codec = EvidencePlanCompletionRegistryJsonCodec()
    assert codec.dumps(left) == codec.dumps(right)
