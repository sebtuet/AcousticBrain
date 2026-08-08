import json
from dataclasses import FrozenInstanceError

import pytest

from acousticbrain.models import SBIRProtocolInstanceInput
from acousticbrain.persistence import SBIRProtocolInstanceInputJsonLoader


PLAN_ID = (
    "EVIDENCE_ACQUISITION_SBIR_PLACEMENT_INTERACTION_REASONING_"
    "ACQUIRE_SUPPORTING_OBSERVATION_V2"
)
FINGERPRINT = "1" * 64


def payload(**overrides):
    value = {
        "schema_version": 1,
        "protocol_instance_id": "sbir-protocol-instance-001",
        "protocol_id": "protocol.temporary_move_speaker.v1",
        "source_plan_id": PLAN_ID,
        "source_plan_contract_fingerprint": FINGERPRINT,
        "reference_experiment_id": "baseline",
        "moved_experiment_id": "exp-sbir-001",
        "speaker_id": "left",
        "surface_id": "front_wall",
        "geometry_candidate_id": "geometry-candidate-001",
        "speaker_displacement_m": 0.12,
        "declaration_source": "STRUCTURED_SCIENTIFIC_SOURCE",
        "user_note": None,
    }
    value.update(overrides)
    return value


def test_loader_round_trips_one_complete_immutable_input(tmp_path):
    loader = SBIRProtocolInstanceInputJsonLoader()
    path = tmp_path / "sbir-instance.json"
    path.write_text(json.dumps(payload()), encoding="utf-8")

    value = loader.load(path)

    assert value == SBIRProtocolInstanceInput(**payload())
    assert loader.decode(json.loads(loader.dumps(value))) == value
    with pytest.raises(FrozenInstanceError):
        value.speaker_id = "right"


def test_identical_documents_decode_deterministically():
    loader = SBIRProtocolInstanceInputJsonLoader()

    first = loader.decode(payload())
    second = loader.decode(dict(reversed(tuple(payload().items()))))

    assert first == second
    assert hash(first) == hash(second)


def test_every_field_is_required():
    loader = SBIRProtocolInstanceInputJsonLoader()
    for field in payload():
        value = payload()
        del value[field]
        with pytest.raises(
            ValueError,
            match=f"Missing SBIR protocol-instance fields: {field}",
        ):
            loader.decode(value)


def test_unknown_fields_are_rejected_in_sorted_order():
    with pytest.raises(ValueError) as error:
        SBIRProtocolInstanceInputJsonLoader().decode(
            payload(z_field="value", a_field="value")
        )
    assert str(error.value) == (
        "Unknown SBIR protocol-instance fields: a_field, z_field"
    )


@pytest.mark.parametrize("version", (None, True, 0, 2, "1"))
def test_schema_version_is_closed(version):
    with pytest.raises(ValueError, match="Unsupported SBIR protocol-instance"):
        SBIRProtocolInstanceInputJsonLoader().decode(
            payload(schema_version=version)
        )


@pytest.mark.parametrize(
    ("field", "invalid"),
    (
        ("protocol_id", "protocol.other.v1"),
        ("source_plan_id", "OTHER_PLAN"),
        ("declaration_source", "USER_JSON"),
    ),
)
def test_contract_values_are_closed(field, invalid):
    with pytest.raises(ValueError, match=f"{field} must be exactly"):
        SBIRProtocolInstanceInputJsonLoader().decode(
            payload(**{field: invalid})
        )


@pytest.mark.parametrize(
    "field",
    (
        "protocol_instance_id",
        "protocol_id",
        "source_plan_id",
        "reference_experiment_id",
        "moved_experiment_id",
        "speaker_id",
        "surface_id",
        "geometry_candidate_id",
        "declaration_source",
    ),
)
@pytest.mark.parametrize("invalid", (None, 1, True, (), []))
def test_exact_text_field_types_are_explicit(field, invalid):
    with pytest.raises(TypeError, match=f"field {field} must be a string"):
        SBIRProtocolInstanceInputJsonLoader().decode(
            payload(**{field: invalid})
        )


@pytest.mark.parametrize(
    "field",
    (
        "protocol_instance_id",
        "protocol_id",
        "source_plan_id",
        "reference_experiment_id",
        "moved_experiment_id",
        "speaker_id",
        "surface_id",
        "geometry_candidate_id",
        "declaration_source",
    ),
)
@pytest.mark.parametrize("invalid", ("", " value "))
def test_text_is_never_normalized_or_inferred(field, invalid):
    with pytest.raises(ValueError, match=f"field {field} must be an exact"):
        SBIRProtocolInstanceInputJsonLoader().decode(
            payload(**{field: invalid})
        )


@pytest.mark.parametrize(
    "fingerprint",
    (None, "", "1" * 63, "1" * 65, "A" * 64, "g" * 64),
)
def test_fingerprint_must_be_canonical_sha256(fingerprint):
    with pytest.raises(ValueError, match="fingerprint must be canonical SHA-256"):
        SBIRProtocolInstanceInputJsonLoader().decode(
            payload(source_plan_contract_fingerprint=fingerprint)
        )


def test_reference_and_moved_experiments_must_differ():
    with pytest.raises(ValueError, match="experiments must differ"):
        SBIRProtocolInstanceInputJsonLoader().decode(
            payload(moved_experiment_id="baseline")
        )


@pytest.mark.parametrize(
    "displacement",
    (None, True, False, "0.12", 0, 0.0, float("nan"), float("inf"), -float("inf")),
)
def test_displacement_must_be_a_finite_nonzero_number(displacement):
    with pytest.raises(ValueError, match="finite, non-zero JSON number"):
        SBIRProtocolInstanceInputJsonLoader().decode(
            payload(speaker_displacement_m=displacement)
        )


@pytest.mark.parametrize("displacement", (-1, 1, -0.12, 0.12))
def test_finite_nonzero_numeric_displacements_are_preserved(displacement):
    value = SBIRProtocolInstanceInputJsonLoader().decode(
        payload(speaker_displacement_m=displacement)
    )
    assert value.speaker_displacement_m == displacement
    assert type(value.speaker_displacement_m) is type(displacement)


@pytest.mark.parametrize("user_note", (1, True, (), []))
def test_user_note_type_is_explicit(user_note):
    with pytest.raises(TypeError, match="user_note must be text or null"):
        SBIRProtocolInstanceInputJsonLoader().decode(payload(user_note=user_note))


@pytest.mark.parametrize("user_note", ("", " note "))
def test_user_note_is_never_normalized(user_note):
    with pytest.raises(ValueError, match="user_note must be null or exact"):
        SBIRProtocolInstanceInputJsonLoader().decode(payload(user_note=user_note))


def test_invalid_non_object_duplicate_and_nonstandard_json_are_rejected(tmp_path):
    loader = SBIRProtocolInstanceInputJsonLoader()

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid SBIR protocol-instance JSON"):
        loader.load(invalid)

    with pytest.raises(ValueError, match="input must be an object"):
        loader.decode([payload()])

    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema_version": 1, "schema_version": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate JSON field: schema_version"):
        loader.load(duplicate)

    nonstandard = tmp_path / "nonstandard.json"
    nonstandard.write_text(
        json.dumps(payload()).replace("0.12", "NaN"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Non-standard JSON number: NaN"):
        loader.load(nonstandard)


def test_loader_has_no_repository_or_write_operation():
    loader = SBIRProtocolInstanceInputJsonLoader()

    assert not hasattr(loader, "save")
    assert not hasattr(loader, "repository")
