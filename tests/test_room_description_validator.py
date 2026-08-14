import pytest

from acousticbrain.models import (
    ListeningPosition,
    RoomDescription,
    RoomDescriptionEntityType,
    RoomDescriptionValidationCode,
    RoomDimensions,
    RoomOpening,
    RoomOpeningSurface,
    SpeakerPosition,
)
from acousticbrain.validation import RoomDescriptionValidator


def opening(
    opening_id,
    surface=RoomOpeningSurface.FRONT_WALL,
    horizontal=0.0,
    vertical=0.0,
    width=1.0,
    height=2.0,
):
    return RoomOpening(
        opening_id,
        surface,
        horizontal,
        vertical,
        width,
        height,
    )


def description(**changes):
    values = {
        "name": "Listening room",
        "dimensions": RoomDimensions(5.0, 4.0, 2.5),
        "speakers": (),
        "listening_positions": (),
        "openings": (),
    }
    values.update(changes)
    return RoomDescription(**values)


def test_accepts_points_on_inclusive_room_boundaries():
    room = description(
        speakers=(SpeakerPosition("LEFT", 0.0, 0.0, 0.0),),
        listening_positions=(ListeningPosition("MAIN", 5.0, 4.0, 2.5),),
    )

    result = RoomDescriptionValidator().validate(room)

    assert result.is_valid
    assert result.errors == ()
    assert result.error_codes == ()


def test_reports_speaker_and_listening_position_outside_the_volume():
    room = description(
        speakers=(SpeakerPosition("LEFT", 5.1, 1.0, 1.0),),
        listening_positions=(ListeningPosition("MAIN", 3.0, 4.1, 2.6),),
    )

    result = RoomDescriptionValidator().validate(room)

    assert result.error_codes == (
        RoomDescriptionValidationCode.SPEAKER_OUTSIDE_ROOM,
        RoomDescriptionValidationCode.LISTENING_POSITION_OUTSIDE_ROOM,
    )
    assert result.errors[0].entity_type is RoomDescriptionEntityType.SPEAKER
    assert result.errors[0].entity_ids == ("LEFT",)
    assert result.errors[0].fields == ("x_m",)
    assert result.errors[1].fields == ("y_m", "z_m")
    assert not hasattr(result.errors[0], "message")


@pytest.mark.parametrize(
    "surface,horizontal_limit",
    [
        (RoomOpeningSurface.FRONT_WALL, 4.0),
        (RoomOpeningSurface.REAR_WALL, 4.0),
        (RoomOpeningSurface.LEFT_WALL, 5.0),
        (RoomOpeningSurface.RIGHT_WALL, 5.0),
    ],
)
def test_accepts_opening_bounds_that_fit_the_declared_surface(
    surface,
    horizontal_limit,
):
    room = description(
        openings=(
            opening(
                "FULL_HEIGHT_EDGE",
                surface,
                horizontal=horizontal_limit - 1.0,
                vertical=0.5,
                width=1.0,
                height=2.0,
            ),
        )
    )

    assert RoomDescriptionValidator().validate(room).is_valid


def test_reports_opening_bounds_outside_the_declared_wall_dimensions():
    room = description(
        openings=(
            opening(
                "DOOR",
                RoomOpeningSurface.FRONT_WALL,
                horizontal=3.5,
                vertical=1.0,
                width=1.0,
                height=2.0,
            ),
        )
    )

    error = RoomDescriptionValidator().validate(room).errors[0]

    assert error.code is RoomDescriptionValidationCode.OPENING_OUTSIDE_SURFACE
    assert error.entity_ids == ("DOOR",)
    assert error.fields == (
        "horizontal_offset_m",
        "width_m",
        "vertical_offset_m",
        "height_m",
    )


def test_detects_positive_area_overlap_on_the_same_surface():
    room = description(
        openings=(
            opening("DOOR", horizontal=0.5, width=1.0),
            opening(
                "WINDOW",
                horizontal=1.0,
                vertical=1.0,
                width=1.5,
                height=1.4,
            ),
        )
    )

    error = RoomDescriptionValidator().validate(room).errors[0]

    assert error.code is RoomDescriptionValidationCode.OPENING_OVERLAP
    assert error.entity_ids == ("DOOR", "WINDOW")


def test_touching_edges_and_different_surfaces_do_not_overlap():
    room = description(
        openings=(
            opening("FIRST", horizontal=0.0, width=1.0),
            opening("TOUCHING", horizontal=1.0, width=1.0),
            opening(
                "OTHER_WALL",
                RoomOpeningSurface.REAR_WALL,
                horizontal=0.5,
                width=1.0,
            ),
        )
    )

    assert RoomDescriptionValidator().validate(room).is_valid


def test_reports_each_overlapping_pair_deterministically():
    room = description(
        openings=(
            opening("C", horizontal=0.2, width=1.0),
            opening("A", horizontal=0.0, width=1.0),
            opening("B", horizontal=0.1, width=1.0),
        )
    )

    result = RoomDescriptionValidator().validate(room)

    assert [error.entity_ids for error in result.errors] == [
        ("A", "B"),
        ("A", "C"),
        ("B", "C"),
    ]


def test_defensively_rejects_zero_area_if_a_model_is_corrupted():
    corrupted = opening("CORRUPTED")
    object.__setattr__(corrupted, "width_m", 0.0)
    room = description(openings=(corrupted,))

    error = RoomDescriptionValidator().validate(room).errors[0]

    assert error.code is RoomDescriptionValidationCode.OPENING_ZERO_AREA
    assert error.fields == ("width_m",)


def test_validator_accepts_only_room_description():
    with pytest.raises(TypeError, match="RoomDescription"):
        RoomDescriptionValidator().validate(object())
