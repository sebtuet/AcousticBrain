import json
from dataclasses import replace

import pytest

from acousticbrain.application import EvidencePlanPreparationDeclarationService
from acousticbrain.models import (
    EvidencePlanPreparationRecord,
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from acousticbrain.persistence import (
    EvidencePlanPreparationRegistryJsonCodec,
    EvidencePlanPreparationRegistryJsonRepository,
)
from test_evidence_plan_preparation_declaration import resolution


def record(*statuses):
    declaration = EvidencePlanPreparationDeclarationService().declare(
        resolution(*statuses)
    )
    return EvidencePlanPreparationRecord.from_declaration(declaration)


def test_registry_round_trip_preserves_input_provenance_and_all_decisions():
    value = record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    registry = EvidencePlanPreparationRegistry().with_record(value)
    codec = EvidencePlanPreparationRegistryJsonCodec()

    restored = codec.loads(codec.dumps(registry))

    assert restored == registry
    assert restored.records[0].confirmation_input.plan_contract_fingerprint == (
        value.confirmation_input.plan_contract_fingerprint
    )


def test_missing_registry_is_empty_and_save_is_atomic_and_idempotent(tmp_path):
    path = tmp_path / "state" / "preparations.json"
    repository = EvidencePlanPreparationRegistryJsonRepository()
    registry = EvidencePlanPreparationRegistry().with_record(record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    ))
    assert repository.load(path) == EvidencePlanPreparationRegistry()

    assert repository.save(path, registry) is True
    before = path.stat().st_mtime_ns
    assert repository.save(path, registry) is False
    assert path.stat().st_mtime_ns == before
    assert not path.with_suffix(".json.tmp").exists()
    assert repository.load(path) == registry


def test_identical_recording_is_an_idempotent_registry_operation():
    first = record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    registry = EvidencePlanPreparationRegistry().with_record(first)
    assert registry.with_record(record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )) is registry


def test_divergent_confirmation_id_reports_sorted_incompatible_fields():
    first = record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    changed_input = replace(
        first.confirmation_input,
        declaration_source="SECOND_USER_JSON",
        user_note="different",
    )
    divergent = replace(first, confirmation_input=changed_input)

    with pytest.raises(ValueError) as error:
        EvidencePlanPreparationRegistry().with_record(first).with_record(divergent)

    assert str(error.value) == (
        "PREPARATION_CONFIRMATION_DIVERGENT: incompatible fields: "
        "confirmation_input.declaration_source, confirmation_input.user_note"
    )


def test_new_confirmation_id_for_same_plan_is_preserved_separately():
    first = record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    second = replace(
        first,
        confirmation_input=replace(
            first.confirmation_input,
            confirmation_id="preparation-confirmation-002",
        ),
    )
    registry = (
        EvidencePlanPreparationRegistry().with_record(second).with_record(first)
    )
    assert tuple(
        value.confirmation_input.confirmation_id for value in registry.records
    ) == ("preparation-confirmation-001", "preparation-confirmation-002")


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (lambda value: value.update(unknown=True), "Unknown registry fields"),
        (lambda value: value.pop("records"), "Missing registry fields"),
        (
            lambda value: value["records"][0].update(extra=True),
            "Unknown record fields",
        ),
    ),
)
def test_registry_json_rejects_invalid_contracts(mutation, message):
    codec = EvidencePlanPreparationRegistryJsonCodec()
    payload = json.loads(codec.dumps(EvidencePlanPreparationRegistry().with_record(
        record(
            EvidencePlanPrerequisiteStatus.CONFIRMED,
            EvidencePlanPrerequisiteStatus.UNKNOWN,
        )
    )))
    mutation(payload)
    with pytest.raises(ValueError, match=message):
        codec.loads(json.dumps(payload))


def test_validation_failure_preserves_existing_registry_file(tmp_path):
    path = tmp_path / "preparations.json"
    path.write_text("original\n", encoding="utf-8")
    with pytest.raises(TypeError, match="registry is required"):
        EvidencePlanPreparationRegistryJsonRepository().save(path, object())
    assert path.read_text(encoding="utf-8") == "original\n"
