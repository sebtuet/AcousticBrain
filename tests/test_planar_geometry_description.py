from dataclasses import FrozenInstanceError

import pytest

from acousticbrain.models import (
    PlanarRegionDescription,
    PlanarRegionRole,
    PlanarSurfaceDescription,
    PlanarSurfaceRole,
    PlanarVertexDescription,
    RoomDescription,
    RoomDimensions,
)


def vertices():
    return (
        PlanarVertexDescription(0.0, 0.0, 0.0),
        PlanarVertexDescription(0.0, 2.0, 0.0),
        PlanarVertexDescription(0.0, 2.0, 2.0),
        PlanarVertexDescription(0.0, 0.0, 2.0),
    )


def test_room_description_preserves_immutable_planar_facts():
    surface = PlanarSurfaceDescription(
        "front_wall_real", PlanarSurfaceRole.FRONT_WALL, vertices()
    )
    region = PlanarRegionDescription(
        "window_1",
        surface.surface_id,
        PlanarRegionRole.OPENING,
        vertices(),
    )
    description = RoomDescription(
        "room",
        RoomDimensions(4.0, 3.0, 2.5),
        planar_surfaces=(surface,),
        planar_regions=(region,),
    )

    assert description.planar_surfaces == (surface,)
    assert description.planar_regions == (region,)
    with pytest.raises(FrozenInstanceError):
        surface.surface_id = "changed"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.1, True])
def test_planar_vertices_reject_invalid_coordinates(value):
    with pytest.raises(ValueError):
        PlanarVertexDescription(value, 0.0, 0.0)


def test_planar_entities_require_at_least_three_typed_vertices():
    with pytest.raises(ValueError):
        PlanarSurfaceDescription(
            "wall", PlanarSurfaceRole.FRONT_WALL, vertices()[:2]
        )
    with pytest.raises(ValueError):
        PlanarRegionDescription(
            "opening", "wall", PlanarRegionRole.OPENING, vertices()[:2]
        )


@pytest.mark.parametrize("field", ["planar_surfaces", "planar_regions"])
def test_room_description_rejects_duplicate_planar_identifiers(field):
    surface = PlanarSurfaceDescription(
        "wall", PlanarSurfaceRole.FRONT_WALL, vertices()
    )
    region = PlanarRegionDescription(
        "region", "wall", PlanarRegionRole.OPENING, vertices()
    )
    values = (surface, surface) if field == "planar_surfaces" else (region, region)

    with pytest.raises(ValueError):
        RoomDescription(
            "room",
            RoomDimensions(4.0, 3.0, 2.5),
            **{field: values},
        )
