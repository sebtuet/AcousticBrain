import json
from dataclasses import replace

import pytest

from acousticbrain.application import SBIRProtocolInstanceRecordingService
from acousticbrain.models import (
    SBIRProtocolInstanceRecord,
    SBIRProtocolInstanceRegistry,
)
from acousticbrain.persistence import (
    SBIRProtocolInstanceRegistryJsonCodec,
    SBIRProtocolInstanceRegistryJsonRepository,
)
from test_sbir_protocol_instance_compatibility import validate


def record():
    return SBIRProtocolInstanceRecord.from_compatibility(validate())


def test_record_preserves_complete_resolved_provenance():
    value = record()
    source = value.protocol_instance_input
    assert value.source_plan_id == source.source_plan_id
    assert value.source_plan_contract_fingerprint == (
        source.source_plan_contract_fingerprint
    )
    assert value.protocol_id == source.protocol_id
    assert value.reference_experiment_id == source.reference_experiment_id
    assert value.moved_experiment_id == source.moved_experiment_id
    assert value.geometry_candidate_id == source.geometry_candidate_id
    assert value.displacement_proposal_id == "proposal-sbir-001"


def test_registry_round_trip_preserves_the_complete_record():
    registry = SBIRProtocolInstanceRegistry().with_record(record())
    codec = SBIRProtocolInstanceRegistryJsonCodec()
    assert codec.loads(codec.dumps(registry)) == registry


def test_identical_recording_is_idempotent():
    first = record()
    registry = SBIRProtocolInstanceRegistry().with_record(first)
    assert registry.with_record(record()) is registry


def test_serialization_order_is_deterministic():
    first = record()
    second = replace(
        first,
        protocol_instance_input=replace(
            first.protocol_instance_input,
            protocol_instance_id="sbir-protocol-instance-002",
        ),
    )
    codec = SBIRProtocolInstanceRegistryJsonCodec()
    left = SBIRProtocolInstanceRegistry((second, first))
    right = SBIRProtocolInstanceRegistry((first, second))
    assert codec.dumps(left) == codec.dumps(right)


def test_divergent_instance_id_reports_sorted_incompatible_fields():
    first = record()
    divergent = replace(
        first,
        protocol_instance_input=replace(
            first.protocol_instance_input,
            user_note="Different declaration",
        ),
    )
    with pytest.raises(ValueError) as error:
        SBIRProtocolInstanceRegistry().with_record(first).with_record(divergent)
    assert str(error.value) == (
        "SBIR_PROTOCOL_INSTANCE_DIVERGENT: incompatible fields: "
        "protocol_instance_input.user_note"
    )


def test_repository_save_is_atomic_and_byte_idempotent(tmp_path):
    path = tmp_path / "state" / "sbir-protocol-instances.json"
    repository = SBIRProtocolInstanceRegistryJsonRepository()
    registry = SBIRProtocolInstanceRegistry().with_record(record())
    assert repository.load(path) == SBIRProtocolInstanceRegistry()
    assert repository.save(path, registry) is True
    first = path.read_bytes()
    first_mtime = path.stat().st_mtime_ns
    assert repository.save(path, registry) is False
    assert path.read_bytes() == first
    assert path.stat().st_mtime_ns == first_mtime
    assert repository.load(path) == registry
    assert not path.with_suffix(".json.tmp").exists()


def test_recording_service_reports_first_write_and_identical_replay(tmp_path):
    path = tmp_path / "sbir-protocol-instances.json"
    service = SBIRProtocolInstanceRecordingService()
    first = service.record(validate(), registry_path=path)
    second = service.record(validate(), registry_path=path)
    assert first.persisted is True
    assert second.persisted is False
    assert first.record == second.record
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1


def test_divergent_recording_preserves_existing_registry(tmp_path):
    path = tmp_path / "sbir-protocol-instances.json"
    service = SBIRProtocolInstanceRecordingService()
    compatibility = validate()
    service.record(compatibility, registry_path=path)
    before = path.read_bytes()
    changed_input = replace(
        compatibility.resolution.protocol_instance_input,
        user_note="Different declaration",
    )
    changed_resolution = replace(
        compatibility.resolution,
        protocol_instance_input=changed_input,
    )
    changed = replace(compatibility, resolution=changed_resolution)
    with pytest.raises(ValueError, match="SBIR_PROTOCOL_INSTANCE_DIVERGENT"):
        service.record(changed, registry_path=path)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (lambda value: value.update(schema_version=2), "Unsupported"),
        (lambda value: value.update(unknown=True), "Unknown registry fields"),
        (lambda value: value.pop("records"), "Missing registry fields"),
    ),
)
def test_registry_json_rejects_invalid_root_contracts(mutation, message):
    payload = json.loads(
        SBIRProtocolInstanceRegistryJsonCodec().dumps(
            SBIRProtocolInstanceRegistry()
        )
    )
    mutation(payload)
    with pytest.raises(ValueError, match=message):
        SBIRProtocolInstanceRegistryJsonCodec().loads(json.dumps(payload))


def test_registry_has_no_manifest_or_experiment_operation(tmp_path):
    path = tmp_path / "sbir-protocol-instances.json"
    result = SBIRProtocolInstanceRecordingService().record(
        validate(),
        registry_path=path,
    )
    assert result.persisted is True
    assert tuple(tmp_path.iterdir()) == (path,)
