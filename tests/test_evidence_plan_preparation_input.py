import json

import pytest

from acousticbrain.models import (
    EvidencePlanPreparationConfirmationInput,
    EvidencePlanPrerequisiteDeclaration,
    EvidencePlanPrerequisiteStatus,
)
from acousticbrain.persistence import (
    EvidencePlanPreparationConfirmationJsonLoader,
)


def payload(**changes):
    value = {
        "schema_version": 1,
        "confirmation_id": "preparation-confirmation-001",
        "plan_id": "READY_PLAN",
        "plan_contract_fingerprint": "a" * 64,
        "prerequisites": [
            {"code": "same_gain", "status": "UNKNOWN"},
            {"code": "documented_microphone_position", "status": "CONFIRMED"},
        ],
        "declaration_source": "USER_JSON",
    }
    value.update(changes)
    return value


def test_loader_decodes_and_canonicalizes_prerequisite_order(tmp_path):
    path = tmp_path / "confirmation.json"
    path.write_text(json.dumps(payload()), encoding="utf-8")

    result = EvidencePlanPreparationConfirmationJsonLoader().load(path)

    assert result.confirmation_id == "preparation-confirmation-001"
    assert tuple(value.code for value in result.prerequisites) == (
        "documented_microphone_position",
        "same_gain",
    )
    assert result.prerequisites[0].status is (
        EvidencePlanPrerequisiteStatus.CONFIRMED
    )
    assert result.prerequisites[1].status is EvidencePlanPrerequisiteStatus.UNKNOWN


def test_semantically_identical_order_produces_the_same_immutable_input():
    loader = EvidencePlanPreparationConfirmationJsonLoader()
    first = loader.decode(payload())
    reversed_payload = payload(prerequisites=list(reversed(payload()["prerequisites"])))
    assert loader.decode(reversed_payload) == first


@pytest.mark.parametrize(
    "status",
    ("CONFIRMED", "NOT_CONFIRMED", "UNKNOWN"),
)
def test_status_vocabulary_is_closed_and_preserved(status):
    result = EvidencePlanPreparationConfirmationJsonLoader().decode(payload(
        prerequisites=[{"code": "same_gain", "status": status}],
    ))
    assert result.prerequisites[0].status.value == status


@pytest.mark.parametrize("status", ("READY", "", None, 1, True))
def test_invalid_prerequisite_status_is_explicit(status):
    with pytest.raises(ValueError, match=r"prerequisite\[0\] status"):
        EvidencePlanPreparationConfirmationJsonLoader().decode(payload(
            prerequisites=[{"code": "same_gain", "status": status}],
        ))


@pytest.mark.parametrize(
    "mutation, message",
    (
        (lambda value: value.pop("plan_id"), "Missing.*input fields: plan_id"),
        (lambda value: value.update(extra=True), "Unknown.*input fields: extra"),
        (lambda value: value.update(schema_version=2), "Unsupported.*version"),
        (lambda value: value.update(schema_version=True), "Unsupported.*version"),
        (lambda value: value.update(prerequisites={}), "must be a list"),
    ),
)
def test_root_contract_errors_are_distinct(mutation, message):
    value = payload()
    mutation(value)
    with pytest.raises(ValueError, match=message):
        EvidencePlanPreparationConfirmationJsonLoader().decode(value)


def test_nested_contract_rejects_missing_and_unknown_fields():
    loader = EvidencePlanPreparationConfirmationJsonLoader()
    with pytest.raises(ValueError, match=r"Missing.*prerequisite\[0\].*status"):
        loader.decode(payload(prerequisites=[{"code": "same_gain"}]))
    with pytest.raises(ValueError, match=r"Unknown.*prerequisite\[0\].*note"):
        loader.decode(payload(prerequisites=[{
            "code": "same_gain", "status": "CONFIRMED", "note": "invented",
        }]))


def test_duplicate_prerequisite_codes_are_rejected():
    with pytest.raises(ValueError, match="codes must be unique"):
        EvidencePlanPreparationConfirmationJsonLoader().decode(payload(
            prerequisites=[
                {"code": "same_gain", "status": "CONFIRMED"},
                {"code": "same_gain", "status": "UNKNOWN"},
            ],
        ))


@pytest.mark.parametrize(
    "fingerprint",
    ("a" * 63, "A" * 64, "g" * 64, None),
)
def test_fingerprint_must_be_canonical_sha256(fingerprint):
    with pytest.raises(ValueError, match="canonical SHA-256"):
        EvidencePlanPreparationConfirmationJsonLoader().decode(payload(
            plan_contract_fingerprint=fingerprint,
        ))


def test_optional_note_is_archival_exact_text():
    result = EvidencePlanPreparationConfirmationJsonLoader().decode(payload(
        user_note="Position repérée au sol",
    ))
    assert result.user_note == "Position repérée au sol"
    with pytest.raises(ValueError, match="user note"):
        EvidencePlanPreparationConfirmationJsonLoader().decode(payload(
            user_note=" padded ",
        ))


def test_model_is_frozen_and_requires_typed_prerequisites():
    value = EvidencePlanPreparationConfirmationJsonLoader().decode(payload())
    with pytest.raises(Exception):
        value.plan_id = "OTHER"
    with pytest.raises(TypeError, match="typed and immutable"):
        EvidencePlanPreparationConfirmationInput(
            schema_version=1,
            confirmation_id="confirmation",
            plan_id="READY_PLAN",
            plan_contract_fingerprint="a" * 64,
            prerequisites=(object(),),
            declaration_source="TEST",
        )


def test_prerequisite_declaration_rejects_normalized_or_untyped_values():
    with pytest.raises(ValueError, match="exact non-empty"):
        EvidencePlanPrerequisiteDeclaration(
            code=" same_gain ",
            status=EvidencePlanPrerequisiteStatus.CONFIRMED,
        )
    with pytest.raises(ValueError, match="status is invalid"):
        EvidencePlanPrerequisiteDeclaration(code="same_gain", status="CONFIRMED")


def test_invalid_json_file_is_explicit(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid evidence-plan preparation JSON"):
        EvidencePlanPreparationConfirmationJsonLoader().load(path)
