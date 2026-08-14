import json

import pytest

from acousticbrain.models import (
    EvidencePlanCompletionInput,
    EvidencePlanCompletionReferenceKind,
)
from acousticbrain.persistence import EvidencePlanCompletionInputJsonLoader


def payload(**overrides):
    value = {
        "schema_version": 1,
        "completion_input_id": "completion-input-001",
        "source_plan_id": "source-plan-001",
        "reference_kind": "PROTOCOL",
        "reference_id": "protocol.example.v1",
        "declaration_source": "USER_JSON",
        "user_note": None,
    }
    value.update(overrides)
    return value


def test_loader_decodes_one_complete_structured_input(tmp_path):
    path = tmp_path / "completion.json"
    path.write_text(json.dumps(payload()), encoding="utf-8")

    value = EvidencePlanCompletionInputJsonLoader().load(path)

    assert value == EvidencePlanCompletionInput(
        schema_version=1,
        completion_input_id="completion-input-001",
        source_plan_id="source-plan-001",
        reference_kind=EvidencePlanCompletionReferenceKind.PROTOCOL,
        reference_id="protocol.example.v1",
        declaration_source="USER_JSON",
        user_note=None,
    )


def test_identical_documents_always_decode_to_the_same_object():
    loader = EvidencePlanCompletionInputJsonLoader()
    first = loader.decode(payload())
    second = loader.decode(dict(reversed(tuple(payload().items()))))

    assert first == second
    assert hash(first) == hash(second)


@pytest.mark.parametrize("reference_kind", ("PROTOCOL", "PLAN"))
def test_reference_kinds_remain_explicit_and_distinct(reference_kind):
    value = EvidencePlanCompletionInputJsonLoader().decode(
        payload(reference_kind=reference_kind)
    )
    assert value.reference_kind.value == reference_kind


def test_unknown_fields_are_rejected_in_sorted_order():
    with pytest.raises(ValueError) as error:
        EvidencePlanCompletionInputJsonLoader().decode(
            payload(z_field="value", a_field="value")
        )
    assert str(error.value) == (
        "Unknown evidence-plan completion fields: a_field, z_field"
    )


def test_missing_fields_are_rejected_in_sorted_order():
    value = payload()
    del value["reference_id"]
    del value["completion_input_id"]
    with pytest.raises(ValueError) as error:
        EvidencePlanCompletionInputJsonLoader().decode(value)
    assert str(error.value) == (
        "Missing evidence-plan completion fields: completion_input_id, reference_id"
    )


@pytest.mark.parametrize("version", (None, True, 0, 2, "1"))
def test_unsupported_schema_versions_are_rejected(version):
    with pytest.raises(ValueError, match="Unsupported evidence-plan completion"):
        EvidencePlanCompletionInputJsonLoader().decode(
            payload(schema_version=version)
        )


@pytest.mark.parametrize("reference_kind", (None, "", "OTHER", 1))
def test_unknown_reference_kind_is_rejected(reference_kind):
    with pytest.raises(ValueError, match="must be PROTOCOL or PLAN"):
        EvidencePlanCompletionInputJsonLoader().decode(
            payload(reference_kind=reference_kind)
        )


@pytest.mark.parametrize(
    "field",
    (
        "completion_input_id",
        "source_plan_id",
        "reference_id",
        "declaration_source",
    ),
)
@pytest.mark.parametrize("invalid", (None, 1, True, (), []))
def test_required_identifier_types_are_explicit(field, invalid):
    with pytest.raises(TypeError, match=f"field {field} must be a string"):
        EvidencePlanCompletionInputJsonLoader().decode(
            payload(**{field: invalid})
        )


@pytest.mark.parametrize(
    "field",
    (
        "completion_input_id",
        "source_plan_id",
        "reference_id",
        "declaration_source",
    ),
)
@pytest.mark.parametrize("invalid", ("", " value "))
def test_required_identifiers_are_never_normalized_or_inferred(field, invalid):
    with pytest.raises(ValueError, match=f"field {field} must be an explicit"):
        EvidencePlanCompletionInputJsonLoader().decode(
            payload(**{field: invalid})
        )


def test_source_plan_cannot_reference_itself():
    with pytest.raises(ValueError, match="cannot be the source plan itself"):
        EvidencePlanCompletionInputJsonLoader().decode(payload(
            reference_kind="PLAN",
            reference_id="source-plan-001",
        ))


@pytest.mark.parametrize("user_note", (1, True, (), []))
def test_user_note_type_is_explicit(user_note):
    with pytest.raises(TypeError, match="user note must be text or absent"):
        EvidencePlanCompletionInputJsonLoader().decode(
            payload(user_note=user_note)
        )


@pytest.mark.parametrize("user_note", ("", " note "))
def test_user_note_is_never_normalized(user_note):
    with pytest.raises(ValueError, match="user note must be absent"):
        EvidencePlanCompletionInputJsonLoader().decode(
            payload(user_note=user_note)
        )


def test_invalid_json_and_non_object_documents_are_explicit(tmp_path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid evidence-plan completion JSON"):
        EvidencePlanCompletionInputJsonLoader().load(invalid)

    with pytest.raises(ValueError, match="must be an object"):
        EvidencePlanCompletionInputJsonLoader().decode([payload()])
