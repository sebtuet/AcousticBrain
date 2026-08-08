import json
from dataclasses import FrozenInstanceError

import pytest

from acousticbrain.models import (
    ListeningPosition,
    RoomDescription,
    RoomDimensions,
    SBIRRoomGeometryDeclarationInput,
    SpeakerPosition,
)
from acousticbrain.persistence import (
    RoomDescriptionJsonCodec,
    SBIRRoomGeometryDeclarationInputJsonLoader,
)


def room_description():
    return RoomDescription(
        name="Measured room",
        dimensions=RoomDimensions(5.0, 4.0, 2.5),
        speakers=(
            SpeakerPosition("LEFT", 0.8, 1.0, 1.1),
            SpeakerPosition("RIGHT", 0.8, 3.0, 1.1),
        ),
        listening_positions=(
            ListeningPosition("LISTENING_POSITION", 3.2, 2.0, 1.2),
        ),
    )


def payload(**overrides):
    value = {
        "schema_version": 1,
        "declaration_input_id": "sbir-room-geometry-001",
        "target_experiment_id": "baseline",
        "declaration_source": "USER_MEASUREMENT",
        "room_description_document": RoomDescriptionJsonCodec().to_dict(
            room_description()
        ),
        "user_note": None,
    }
    value.update(overrides)
    return value


def test_loader_round_trips_one_complete_immutable_input(tmp_path):
    loader = SBIRRoomGeometryDeclarationInputJsonLoader()
    path = tmp_path / "geometry-input.json"
    path.write_text(json.dumps(payload()), encoding="utf-8")
    value = loader.load(path)
    assert value.room_description == room_description()
    assert loader.decode(json.loads(loader.dumps(value))) == value
    with pytest.raises(FrozenInstanceError):
        value.declaration_input_id = "changed"


def test_every_envelope_field_is_required():
    loader = SBIRRoomGeometryDeclarationInputJsonLoader()
    for field in payload():
        value = payload()
        del value[field]
        with pytest.raises(ValueError, match=f"fields: {field}"):
            loader.decode(value)


def test_unknown_envelope_fields_are_rejected_in_sorted_order():
    with pytest.raises(ValueError) as error:
        SBIRRoomGeometryDeclarationInputJsonLoader().decode(
            payload(z_field=True, a_field=True)
        )
    assert str(error.value) == (
        "Unknown SBIR room-geometry fields: a_field, z_field"
    )


@pytest.mark.parametrize("version", (None, True, 0, 2, "1"))
def test_envelope_schema_is_closed(version):
    with pytest.raises(ValueError, match="Unsupported SBIR room-geometry"):
        SBIRRoomGeometryDeclarationInputJsonLoader().decode(
            payload(schema_version=version)
        )


@pytest.mark.parametrize(
    ("field", "invalid", "message"),
    (
        ("target_experiment_id", "exp-001", "exactly baseline"),
        ("declaration_source", "USER_JSON", "exactly USER_MEASUREMENT"),
    ),
)
def test_closed_text_values_are_not_inferred(field, invalid, message):
    with pytest.raises(ValueError, match=message):
        SBIRRoomGeometryDeclarationInputJsonLoader().decode(
            payload(**{field: invalid})
        )


@pytest.mark.parametrize(
    "field",
    ("declaration_input_id", "target_experiment_id", "declaration_source"),
)
@pytest.mark.parametrize("invalid", (None, 1, True, (), []))
def test_text_field_types_are_explicit(field, invalid):
    with pytest.raises(TypeError, match=f"field {field} must be a string"):
        SBIRRoomGeometryDeclarationInputJsonLoader().decode(
            payload(**{field: invalid})
        )


@pytest.mark.parametrize("invalid", ("", " value "))
def test_declaration_identity_is_never_normalized(invalid):
    with pytest.raises(ValueError, match="must be exact non-empty text"):
        SBIRRoomGeometryDeclarationInputJsonLoader().decode(
            payload(declaration_input_id=invalid)
        )


@pytest.mark.parametrize("user_note", (1, True, (), []))
def test_user_note_type_is_explicit(user_note):
    with pytest.raises(TypeError, match="user_note must be text or null"):
        SBIRRoomGeometryDeclarationInputJsonLoader().decode(
            payload(user_note=user_note)
        )


@pytest.mark.parametrize("user_note", ("", " note "))
def test_user_note_is_never_normalized(user_note):
    with pytest.raises(ValueError, match="null or exact non-empty"):
        SBIRRoomGeometryDeclarationInputJsonLoader().decode(
            payload(user_note=user_note)
        )


@pytest.mark.parametrize("version", (1, 4, 5.0, 6, True))
def test_embedded_room_description_must_be_current_v5(version):
    document = RoomDescriptionJsonCodec().to_dict(room_description())
    document["schema_version"] = version
    with pytest.raises(ValueError, match="must use schema version 5"):
        SBIRRoomGeometryDeclarationInputJsonLoader().decode(
            payload(room_description_document=document)
        )


def test_embedded_room_description_must_be_complete_and_canonical():
    document = RoomDescriptionJsonCodec().to_dict(room_description())
    document["unknown"] = True
    with pytest.raises(ValueError, match="must be canonical"):
        SBIRRoomGeometryDeclarationInputJsonLoader().decode(
            payload(room_description_document=document)
        )


def test_invalid_duplicate_and_nonstandard_json_are_rejected(tmp_path):
    loader = SBIRRoomGeometryDeclarationInputJsonLoader()
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid SBIR room-geometry JSON"):
        loader.load(invalid)
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate JSON field"):
        loader.load(duplicate)
    nonstandard = tmp_path / "nonstandard.json"
    nonstandard.write_text('{"value":NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="Non-standard JSON number"):
        loader.load(nonstandard)


def test_loader_has_no_repository_or_write_operation():
    loader = SBIRRoomGeometryDeclarationInputJsonLoader()
    assert not hasattr(loader, "save")
    assert not hasattr(loader, "repository")
