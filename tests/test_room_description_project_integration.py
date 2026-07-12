import json

from acousticbrain.adapters import LegacyRoomAdapter
from acousticbrain.application import RoomDescriptionProjectLoader
from acousticbrain.commands.load_room_description import main
from acousticbrain.models import (
    Room,
    RoomDescription,
    RoomDescriptionPersistenceErrorCode,
    RoomDescriptionValidationCode,
    RoomDimensions,
    SpeakerPosition,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec
from acousticbrain.project import Project


def description(name="Described room"):
    return RoomDescription(
        name=name,
        dimensions=RoomDimensions(6.0, 4.5, 2.7),
        speakers=(SpeakerPosition("LEFT", 1.0, 1.0, 1.1),),
    )


def project(existing_description=None):
    return Project(
        name="Measurements",
        room=Room("Legacy room", 5.0, 4.0, 2.5),
        room_description=existing_description,
    )


def test_explicit_loader_attaches_a_validated_file_without_changing_legacy_room(
    tmp_path,
):
    target = project()
    path = tmp_path / "room.json"
    path.write_text(
        RoomDescriptionJsonCodec().dumps(description()),
        encoding="utf-8",
    )

    result = RoomDescriptionProjectLoader().load(target, path)

    assert result.is_success
    assert target.room_description == description()
    assert target.room.name == "Legacy room"
    assert (target.room.length, target.room.width, target.room.height) == (
        5.0,
        4.0,
        2.5,
    )


def test_failed_load_preserves_the_existing_project_description(tmp_path):
    existing = description("Existing")
    target = project(existing)
    path = tmp_path / "invalid.json"
    path.write_text('{"schema_version": 99}', encoding="utf-8")

    result = RoomDescriptionProjectLoader().load(target, path)

    assert not result.is_success
    assert result.errors[0].code is (
        RoomDescriptionPersistenceErrorCode.UNKNOWN_SCHEMA_VERSION
    )
    assert target.room_description is existing


def test_project_loader_reports_v1_migration_without_rewriting_source(tmp_path):
    target = project()
    payload = RoomDescriptionJsonCodec().to_dict(description())
    payload["schema_version"] = 1
    room = payload["room_description"]
    for speaker in room["speakers"]:
        speaker.pop("orientation")
    for field in (
        "surface_materials",
        "covering_zones",
        "furniture",
        "acoustic_treatments",
    ):
        room.pop(field)
    path = tmp_path / "legacy-v1.json"
    original = json.dumps(payload, sort_keys=True)
    path.write_text(original, encoding="utf-8")

    result = RoomDescriptionProjectLoader().load(target, path)

    assert result.is_success
    assert result.source_schema_version == 1
    assert result.requires_migration
    assert path.read_text(encoding="utf-8") == original
    assert target.room_description.surface_materials == ()


def test_file_access_errors_are_structured_and_do_not_mutate_project(tmp_path):
    target = project()
    missing = tmp_path / "missing.json"

    result = RoomDescriptionProjectLoader().load(target, missing)

    assert result.errors[0].code is (
        RoomDescriptionPersistenceErrorCode.FILE_NOT_FOUND
    )
    assert result.errors[0].path == (str(missing),)
    assert target.room_description is None

    unreadable_as_file = RoomDescriptionProjectLoader().load(target, tmp_path)
    assert unreadable_as_file.errors[0].code is (
        RoomDescriptionPersistenceErrorCode.FILE_READ_ERROR
    )


def test_legacy_adapter_is_explicit_and_maps_only_declared_dimensions():
    result = LegacyRoomAdapter().adapt(
        description(), temperature_celsius=21.5
    )

    assert result.is_success
    assert result.room.name == "Described room"
    assert result.room.length == 6.0
    assert result.room.width == 4.5
    assert result.room.height == 2.7
    assert result.room.temperature == 21.5


def test_legacy_adapter_refuses_relationally_invalid_description():
    invalid = RoomDescription(
        name="Invalid",
        dimensions=RoomDimensions(5.0, 4.0, 2.5),
        speakers=(SpeakerPosition("OUTSIDE", 50.0, 1.0, 1.0),),
    )

    result = LegacyRoomAdapter().adapt(invalid)

    assert not result.is_success
    assert result.room is None
    assert result.errors[0].code is (
        RoomDescriptionValidationCode.SPEAKER_OUTSIDE_ROOM
    )


def test_command_selects_measurement_and_room_description_paths(
    tmp_path,
    capsys,
):
    measurements = tmp_path / "measurements"
    measurements.mkdir()
    room_file = tmp_path / "room.json"
    room_file.write_text(
        RoomDescriptionJsonCodec().dumps(description()),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--measurements",
            str(measurements),
            "--room-description",
            str(room_file),
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output == {
        "loaded": True,
        "project": "measurements",
        "room_description": "Described room",
        "source_schema_version": 2,
        "target_schema_version": 2,
        "requires_migration": False,
    }


def test_command_returns_structured_errors_for_an_invalid_configuration(
    tmp_path,
    capsys,
):
    measurements = tmp_path / "measurements"
    measurements.mkdir()
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not-json", encoding="utf-8")

    exit_code = main(
        [
            "--measurements",
            str(measurements),
            "--room-description",
            str(invalid),
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["loaded"] is False
    assert output["errors"][0]["code"] == "INVALID_JSON"
