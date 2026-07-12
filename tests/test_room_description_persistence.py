import json

import pytest

from acousticbrain.models import (
    ListeningPosition,
    Room,
    RoomDescription,
    RoomDescriptionPersistenceErrorCode,
    RoomDescriptionPersistenceException,
    RoomDescriptionValidationCode,
    RoomDimensions,
    RoomOpening,
    RoomOpeningSurface,
    SpeakerPosition,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec
from acousticbrain.project import Project


def description():
    return RoomDescription(
        name="Studio",
        dimensions=RoomDimensions(5.0, 4.0, 2.5),
        speakers=(
            SpeakerPosition("LEFT", 0.8, 1.0, 1.1),
            SpeakerPosition("RIGHT", 0.8, 3.0, 1.1),
        ),
        listening_positions=(ListeningPosition("MAIN", 3.2, 2.0, 1.2),),
        openings=(
            RoomOpening(
                "DOOR",
                RoomOpeningSurface.REAR_WALL,
                0.5,
                0.0,
                0.9,
                2.1,
            ),
        ),
    )


def encoded_payload():
    return RoomDescriptionJsonCodec().to_dict(description())


def test_round_trip_preserves_identifiers_types_and_geometry():
    codec = RoomDescriptionJsonCodec()

    payload = codec.dumps(description())
    result = codec.loads(payload)

    assert result.is_success
    assert result.description == description()
    assert result.description.openings[0].surface is RoomOpeningSurface.REAR_WALL
    assert json.loads(payload)["schema_version"] == 1


def test_json_output_is_deterministic_and_versioned():
    codec = RoomDescriptionJsonCodec()

    first = codec.dumps(description(), indent=2)
    second = codec.dumps(description(), indent=2)

    assert first == second
    assert list(json.loads(first)) == ["room_description", "schema_version"]


def test_reports_invalid_json_without_raising_a_parser_error():
    result = RoomDescriptionJsonCodec().loads("{not-json")

    assert not result.is_success
    assert result.errors[0].code is RoomDescriptionPersistenceErrorCode.INVALID_JSON
    assert result.errors[0].path == ()


@pytest.mark.parametrize("version", [0, 2, "1", True])
def test_reports_unknown_or_untyped_schema_versions(version):
    payload = encoded_payload()
    payload["schema_version"] = version

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert result.errors[0].code is (
        RoomDescriptionPersistenceErrorCode.UNKNOWN_SCHEMA_VERSION
    )
    assert result.errors[0].path == ("schema_version",)


def test_reports_a_missing_field_with_its_deterministic_path():
    payload = encoded_payload()
    del payload["room_description"]["dimensions"]["height_m"]

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert result.errors[0].code is RoomDescriptionPersistenceErrorCode.MISSING_FIELD
    assert result.errors[0].path == (
        "room_description",
        "dimensions",
        "height_m",
    )


def test_schema_collections_are_required_even_when_empty():
    payload = encoded_payload()
    del payload["room_description"]["openings"]

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert result.errors[0].code is RoomDescriptionPersistenceErrorCode.MISSING_FIELD
    assert result.errors[0].path == ("room_description", "openings")


@pytest.mark.parametrize(
    "path,value",
    [
        (("dimensions", "length_m"), -1.0),
        (("speakers", 0, "x_m"), "0.8"),
        (("openings", 0, "surface"), "FLOOR"),
        (("openings", 0, "width_m"), 0.0),
    ],
)
def test_reports_invalid_values_with_precise_paths(path, value):
    payload = encoded_payload()
    target = payload["room_description"]
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert result.errors[0].code is RoomDescriptionPersistenceErrorCode.INVALID_VALUE
    assert result.errors[0].path == ("room_description", *path)


def test_runs_relational_validation_and_withholds_invalid_description():
    payload = encoded_payload()
    payload["room_description"]["speakers"][0]["x_m"] = 50.0

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert result.description is None
    error = result.errors[0]
    assert error.code is RoomDescriptionPersistenceErrorCode.INVALID_GEOMETRY
    assert error.validation_code is (
        RoomDescriptionValidationCode.SPEAKER_OUTSIDE_ROOM
    )
    assert error.entity_ids == ("LEFT",)


def test_project_stores_an_optional_description_without_pipeline_side_effects():
    project = Project(
        name="Studio",
        room=Room("Legacy", 5.0, 4.0, 2.5),
        room_description=description(),
    )

    assert project.room_description == description()
    assert project.measurements == {}
    assert project.impulse_responses == {}


def test_serialization_failure_carries_structured_geometry_errors():
    invalid = RoomDescription(
        name="Invalid",
        dimensions=RoomDimensions(5.0, 4.0, 2.5),
        speakers=(SpeakerPosition("OUTSIDE", 50.0, 1.0, 1.0),),
    )

    with pytest.raises(RoomDescriptionPersistenceException) as raised:
        RoomDescriptionJsonCodec().dumps(invalid)

    error = raised.value.errors[0]
    assert error.code is RoomDescriptionPersistenceErrorCode.INVALID_GEOMETRY
    assert error.validation_code is (
        RoomDescriptionValidationCode.SPEAKER_OUTSIDE_ROOM
    )
    with pytest.raises(RoomDescriptionPersistenceException):
        RoomDescriptionJsonCodec().to_dict(invalid)
