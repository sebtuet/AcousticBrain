from dataclasses import FrozenInstanceError
from math import inf, nan

import pytest

from acousticbrain.models import (
    ListeningPosition,
    RoomDescription,
    RoomDimensions,
    RoomOpening,
    RoomOpeningSurface,
    SpeakerPosition,
)


def dimensions():
    return RoomDimensions(length_m=5.0, width_m=4.0, height_m=2.6)


def test_builds_an_immutable_description_independent_from_analyses():
    speaker = SpeakerPosition("LEFT", 0.8, 1.0, 1.1)
    listening = ListeningPosition("MAIN", 3.2, 2.0, 1.2)
    opening = RoomOpening(
        "DOOR",
        RoomOpeningSurface.REAR_WALL,
        horizontal_offset_m=0.5,
        vertical_offset_m=0.0,
        width_m=0.9,
        height_m=2.1,
    )

    description = RoomDescription(
        name="Listening room",
        dimensions=dimensions(),
        speakers=(speaker,),
        listening_positions=(listening,),
        openings=(opening,),
    )

    assert description.speakers == (speaker,)
    assert description.listening_positions == (listening,)
    assert description.openings == (opening,)
    assert RoomOpeningSurface.REAR_WALL.value == "REAR_WALL"
    with pytest.raises(FrozenInstanceError):
        description.name = "Changed"


@pytest.mark.parametrize(
    "values",
    [
        (0.0, 4.0, 2.6),
        (-5.0, 4.0, 2.6),
        (5.0, inf, 2.6),
        (5.0, 4.0, nan),
    ],
)
def test_room_dimensions_require_positive_finite_values(values):
    with pytest.raises(ValueError, match="dimensions"):
        RoomDimensions(*values)


@pytest.mark.parametrize(
    "position_type, identifier_field",
    [
        (SpeakerPosition, "speaker_id"),
        (ListeningPosition, "position_id"),
    ],
)
def test_positions_require_an_identifier_and_non_negative_finite_coordinates(
    position_type,
    identifier_field,
):
    with pytest.raises(ValueError, match="identifier"):
        position_type(**{identifier_field: " ", "x_m": 1.0, "y_m": 1.0, "z_m": 1.0})
    with pytest.raises(ValueError, match="negative"):
        position_type(**{identifier_field: "A", "x_m": -1.0, "y_m": 1.0, "z_m": 1.0})
    with pytest.raises(ValueError, match="finite"):
        position_type(**{identifier_field: "A", "x_m": 1.0, "y_m": inf, "z_m": 1.0})


def test_opening_requires_local_positive_geometry_and_stable_surface():
    with pytest.raises(ValueError, match="offsets"):
        RoomOpening(
            "DOOR", RoomOpeningSurface.LEFT_WALL, -0.1, 0.0, 0.9, 2.1
        )
    with pytest.raises(ValueError, match="dimensions"):
        RoomOpening(
            "DOOR", RoomOpeningSurface.LEFT_WALL, 0.1, 0.0, 0.0, 2.1
        )
    with pytest.raises(ValueError, match="finite"):
        RoomOpening(
            "DOOR", RoomOpeningSurface.LEFT_WALL, 0.1, 0.0, 0.9, nan
        )


@pytest.mark.parametrize(
    "field, duplicate_values",
    [
        (
            "speakers",
            (
                SpeakerPosition("LEFT", 1.0, 1.0, 1.0),
                SpeakerPosition("LEFT", 1.0, 3.0, 1.0),
            ),
        ),
        (
            "listening_positions",
            (
                ListeningPosition("MAIN", 3.0, 2.0, 1.2),
                ListeningPosition("MAIN", 3.5, 2.0, 1.2),
            ),
        ),
        (
            "openings",
            (
                RoomOpening(
                    "DOOR", RoomOpeningSurface.FRONT_WALL, 0.0, 0.0, 0.9, 2.1
                ),
                RoomOpening(
                    "DOOR", RoomOpeningSurface.REAR_WALL, 0.0, 0.0, 0.9, 2.1
                ),
            ),
        ),
    ],
)
def test_description_rejects_duplicate_identifiers_per_category(
    field,
    duplicate_values,
):
    with pytest.raises(ValueError, match="duplicate"):
        RoomDescription(
            name="Room",
            dimensions=dimensions(),
            **{field: duplicate_values},
        )


def test_relational_bounds_are_intentionally_deferred_to_pr020b():
    outside = SpeakerPosition("OUTSIDE", 50.0, 40.0, 20.0)

    description = RoomDescription(
        name="Contract only",
        dimensions=dimensions(),
        speakers=(outside,),
    )

    assert description.speakers == (outside,)
    assert not hasattr(description, "volume")


def test_description_rejects_mutable_collections():
    with pytest.raises(ValueError, match="tuple"):
        RoomDescription(
            name="Mutable",
            dimensions=dimensions(),
            speakers=[SpeakerPosition("LEFT", 1.0, 1.0, 1.0)],
        )


def test_opening_surface_cannot_be_an_untyped_string():
    with pytest.raises(ValueError, match="surface"):
        RoomOpening("DOOR", "FRONT_WALL", 0.0, 0.0, 0.9, 2.1)
