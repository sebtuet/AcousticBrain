import pytest

from acousticbrain.analysis import (
    RoomGeometryBuildException,
    RoomGeometryBuilder,
)
from acousticbrain.models import (
    GeometrySource,
    ListeningPosition,
    Room,
    RoomDescription,
    RoomDimensions,
    RoomGeometryModel,
    RoomOpening,
    RoomOpeningSurface,
    RoomSurfaceKind,
    SpeakerPosition,
)


def description(*, speakers=True, listening=True, openings=()):
    return RoomDescription(
        name="Studio",
        dimensions=RoomDimensions(6.0, 5.0, 2.5),
        speakers=(
            SpeakerPosition("right", 1.0, 4.0, 1.0),
            SpeakerPosition("left", 1.0, 1.0, 1.0),
        ) if speakers else (),
        listening_positions=(
            ListeningPosition("seat", 4.0, 2.5, 1.1),
        ) if listening else (),
        openings=tuple(openings),
    )


def opening(opening_id, surface, horizontal):
    return RoomOpening(
        opening_id=opening_id,
        surface=surface,
        horizontal_offset_m=horizontal,
        vertical_offset_m=0.2,
        width_m=0.5,
        height_m=1.0,
    )


def test_builds_six_rectangular_surfaces_in_stable_order():
    result = RoomGeometryBuilder().from_description(description())

    assert tuple(surface.surface_id for surface in result.surfaces) == (
        "front_wall",
        "rear_wall",
        "left_wall",
        "right_wall",
        "floor",
        "ceiling",
    )
    assert tuple(surface.kind for surface in result.surfaces) == tuple(
        RoomSurfaceKind
    )
    assert [
        (item.origin.x_m, item.origin.y_m, item.origin.z_m)
        for item in result.surfaces
    ] == [
        (0.0, 0.0, 0.0),
        (6.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 5.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 2.5),
    ]
    assert [(item.width_m, item.height_m) for item in result.surfaces] == [
        (5.0, 2.5),
        (5.0, 2.5),
        (6.0, 2.5),
        (6.0, 2.5),
        (6.0, 5.0),
        (6.0, 5.0),
    ]


def test_converts_and_sorts_points_without_changing_coordinates():
    result = RoomGeometryBuilder().from_description(description())

    assert tuple(item.point_id for item in result.speakers) == ("left", "right")
    assert (result.speakers[0].x_m, result.speakers[0].y_m, result.speakers[0].z_m) == (
        1.0,
        1.0,
        1.0,
    )
    assert result.listening_positions[0].point_id == "seat"


def test_attaches_openings_to_each_vertical_surface_deterministically():
    source_openings = (
        opening("right", RoomOpeningSurface.RIGHT_WALL, 2.0),
        opening("front", RoomOpeningSurface.FRONT_WALL, 0.5),
        opening("left", RoomOpeningSurface.LEFT_WALL, 1.0),
        opening("rear", RoomOpeningSurface.REAR_WALL, 1.5),
    )

    result = RoomGeometryBuilder().from_description(
        description(openings=source_openings)
    )

    assert tuple(item.opening_id for item in result.openings) == (
        "front",
        "left",
        "rear",
        "right",
    )
    assert {item.opening_id: item.surface_id for item in result.openings} == {
        "front": "front_wall",
        "rear": "rear_wall",
        "left": "left_wall",
        "right": "right_wall",
    }
    assert result.openings[0].horizontal_offset_m == 0.5
    assert result.openings[0].vertical_offset_m == 0.2


def test_preserves_explicit_source_model_version_and_completeness():
    builder = RoomGeometryBuilder()

    complete = builder.from_description(description())
    partial = builder.from_description(
        description(speakers=False, listening=False)
    )
    legacy = builder.from_legacy_room(Room("Legacy", 6.0, 5.0, 2.5))

    assert complete.source is GeometrySource.ROOM_DESCRIPTION
    assert complete.completeness == 100.0
    assert partial.completeness == 60.0
    assert legacy.source is GeometrySource.LEGACY_ROOM
    assert legacy.completeness == 60.0
    assert complete.model is RoomGeometryModel.RECTANGULAR
    assert complete.model_version == builder.MODEL_VERSION


def test_legacy_and_equivalent_description_have_the_same_geometric_core():
    builder = RoomGeometryBuilder()
    declared = builder.from_description(
        description(speakers=False, listening=False)
    )
    legacy = builder.from_legacy_room(Room("Legacy", 6.0, 5.0, 2.5))

    assert declared.dimensions == legacy.dimensions
    assert declared.surfaces == legacy.surfaces
    assert declared.speakers == legacy.speakers == ()
    assert declared.listening_positions == legacy.listening_positions == ()
    assert declared.openings == legacy.openings == ()
    assert declared.source is not legacy.source


def test_invalid_description_is_refused_without_partial_geometry():
    invalid = description(
        openings=(
            opening("outside", RoomOpeningSurface.FRONT_WALL, 4.8),
        )
    )

    with pytest.raises(RoomGeometryBuildException) as captured:
        RoomGeometryBuilder().from_description(invalid)

    assert captured.value.errors
    assert not hasattr(captured.value, "geometry")


@pytest.mark.parametrize(
    "room",
    [
        Room("Invalid", 0.0, 5.0, 2.5),
        Room("Invalid", float("nan"), 5.0, 2.5),
        Room("Invalid", True, 5.0, 2.5),
    ],
)
def test_invalid_legacy_source_is_refused_without_partial_geometry(room):
    with pytest.raises(ValueError, match="dimensions"):
        RoomGeometryBuilder().from_legacy_room(room)


def test_source_entry_points_are_strict_and_never_fallback():
    builder = RoomGeometryBuilder()

    with pytest.raises(TypeError, match="RoomDescription"):
        builder.from_description(Room("Legacy", 6.0, 5.0, 2.5))
    with pytest.raises(TypeError, match="Room"):
        builder.from_legacy_room(description())
    assert not hasattr(builder, "build")
