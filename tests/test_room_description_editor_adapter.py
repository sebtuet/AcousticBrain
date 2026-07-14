import json

from acousticbrain.models import (
    PlanarSurfaceDescription,
    PlanarSurfaceRole,
    PlanarVertexDescription,
    RoomDescription,
    RoomDescriptionPersistenceErrorCode,
    RoomDimensions,
    RoomDescriptionValidationCode,
    RoomOpeningSurface,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec
from acousticbrain.ui import (
    ListeningPositionFormRow,
    RoomDescriptionEditorAdapter,
    RoomDescriptionFormState,
    RoomOpeningFormRow,
    SpeakerPositionFormRow,
)


def valid_state():
    return RoomDescriptionFormState(
        name="Studio",
        length_m="5.0",
        width_m="4.0",
        height_m="2.5",
        speakers=(
            SpeakerPositionFormRow("LEFT", "0.8", "1.0", "1.1"),
            SpeakerPositionFormRow("RIGHT", "0.8", "3.0", "1.1"),
        ),
        listening_positions=(
            ListeningPositionFormRow("MAIN", "3.2", "2.0", "1.2"),
        ),
        openings=(
            RoomOpeningFormRow(
                "DOOR",
                "REAR_WALL",
                "0.5",
                "0.0",
                "0.9",
                "2.1",
            ),
        ),
    )


def test_adapter_builds_models_only_through_the_validated_codec_path():
    result = RoomDescriptionEditorAdapter().validate(valid_state())

    assert result.is_valid
    assert result.description.name == "Studio"
    assert result.description.speakers[0].speaker_id == "LEFT"
    assert result.description.openings[0].surface is RoomOpeningSurface.REAR_WALL


def test_adapter_reports_numeric_form_errors_with_precise_paths():
    state = valid_state()
    state = RoomDescriptionFormState(
        **(state.__dict__ | {"length_m": "five"})
    )

    result = RoomDescriptionEditorAdapter().validate(state)

    assert not result.is_valid
    assert result.errors[0].code is RoomDescriptionPersistenceErrorCode.INVALID_VALUE
    assert result.errors[0].path == (
        "room_description",
        "dimensions",
        "length_m",
    )


def test_adapter_exposes_immediate_relational_validation_errors():
    state = valid_state()
    outside = SpeakerPositionFormRow("LEFT", "50", "1", "1")
    state = RoomDescriptionFormState(
        **(state.__dict__ | {"speakers": (outside,)})
    )

    result = RoomDescriptionEditorAdapter().validate(state)

    assert result.errors[0].code is (
        RoomDescriptionPersistenceErrorCode.INVALID_GEOMETRY
    )
    assert result.errors[0].validation_code is (
        RoomDescriptionValidationCode.SPEAKER_OUTSIDE_ROOM
    )
    assert result.errors[0].entity_ids == ("LEFT",)


def test_adapter_exposes_opening_overlap_without_ui_specific_rules():
    state = valid_state()
    state = RoomDescriptionFormState(
        **(
            state.__dict__
            | {
                "openings": (
                    RoomOpeningFormRow(
                        "A", "FRONT_WALL", "0", "0", "1", "2"
                    ),
                    RoomOpeningFormRow(
                        "B", "FRONT_WALL", "0.5", "0", "1", "2"
                    ),
                )
            }
        )
    )

    result = RoomDescriptionEditorAdapter().validate(state)

    assert result.errors[0].validation_code is (
        RoomDescriptionValidationCode.OPENING_OVERLAP
    )


def test_serialize_and_load_round_trip_through_room_description_codec():
    adapter = RoomDescriptionEditorAdapter()

    serialized = adapter.serialize(valid_state())
    loaded = adapter.load(serialized.payload)

    assert serialized.is_success
    assert json.loads(serialized.payload)["schema_version"] == 3
    assert loaded.is_success
    assert loaded.state == valid_state()


def test_invalid_form_is_never_serialized_as_partial_json():
    state = RoomDescriptionFormState(
        name="Incomplete",
        length_m="",
        width_m="4",
        height_m="2.5",
    )

    result = RoomDescriptionEditorAdapter().serialize(state)

    assert not result.is_success
    assert result.payload is None
    assert result.errors


def test_load_errors_are_forwarded_without_partial_form_state():
    result = RoomDescriptionEditorAdapter().load('{"schema_version": 99}')

    assert not result.is_success
    assert result.state is None
    assert result.errors[0].code is (
        RoomDescriptionPersistenceErrorCode.UNKNOWN_SCHEMA_VERSION
    )


def test_editor_refuses_planar_scene_instead_of_losing_it_on_round_trip():
    description = RoomDescription(
        "Planar",
        RoomDimensions(5, 4, 3),
        planar_surfaces=(PlanarSurfaceDescription(
            "wall",
            PlanarSurfaceRole.FRONT_WALL,
            (
                PlanarVertexDescription(0, 0, 0),
                PlanarVertexDescription(0, 4, 0),
                PlanarVertexDescription(0, 4, 3),
            ),
        ),),
    )

    result = RoomDescriptionEditorAdapter().load(
        RoomDescriptionJsonCodec().dumps(description)
    )

    assert not result.is_success
    assert result.state is None
    assert result.errors[0].code is (
        RoomDescriptionPersistenceErrorCode.EDITOR_UNSUPPORTED_PLANAR_GEOMETRY
    )
