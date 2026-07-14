import json

from acousticbrain.models import (
    PlanarRegionDescription,
    PlanarRegionRole,
    PlanarSurfaceDescription,
    PlanarSurfaceRole,
    PlanarVertexDescription as Vertex,
    RoomDescription,
    RoomDimensions,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec


def description():
    surface = PlanarSurfaceDescription(
        "oblique_wall",
        PlanarSurfaceRole.LEFT_WALL,
        (Vertex(0, 0, 0), Vertex(4, 0.5, 0), Vertex(4, 0.5, 2.5), Vertex(0, 0, 2.5)),
    )
    region = PlanarRegionDescription(
        "window",
        surface.surface_id,
        PlanarRegionRole.OPENING,
        (Vertex(1, 0.125, 0.5), Vertex(2, 0.25, 0.5), Vertex(2, 0.25, 1.5)),
    )
    return RoomDescription(
        "room",
        RoomDimensions(5.0, 4.0, 3.0),
        planar_surfaces=(surface,),
        planar_regions=(region,),
    )


def test_schema_v3_round_trip_preserves_planar_geometry():
    codec = RoomDescriptionJsonCodec()
    payload = codec.dumps(description())
    result = codec.loads(payload)

    assert json.loads(payload)["schema_version"] == 4
    assert result.description == description()
    assert result.source_schema_version == 4
    assert not result.requires_migration


def test_schema_v3_output_is_independent_from_collection_order():
    codec = RoomDescriptionJsonCodec()
    original = description()
    second = PlanarSurfaceDescription(
        "front", PlanarSurfaceRole.FRONT_WALL,
        (Vertex(0, 0, 0), Vertex(0, 4, 0), Vertex(0, 4, 3)),
    )
    first = RoomDescription(
        original.name, original.dimensions,
        planar_surfaces=(original.planar_surfaces[0], second),
        planar_regions=original.planar_regions,
    )
    reversed_description = RoomDescription(
        original.name, original.dimensions,
        planar_surfaces=tuple(reversed(first.planar_surfaces)),
        planar_regions=first.planar_regions,
    )
    assert codec.dumps(first) == codec.dumps(reversed_description)


def test_schema_v2_loads_without_inventing_planar_geometry():
    codec = RoomDescriptionJsonCodec()
    payload = codec.to_dict(RoomDescription("room", RoomDimensions(5, 4, 3)))
    payload["schema_version"] = 2
    payload["room_description"].pop("planar_surfaces")
    payload["room_description"].pop("planar_regions")

    result = codec.from_dict(payload)

    assert result.description.planar_surfaces == ()
    assert result.description.planar_regions == ()
    assert result.requires_migration


def test_schema_v3_reports_precise_invalid_vertex_path():
    codec = RoomDescriptionJsonCodec()
    payload = codec.to_dict(description())
    payload["room_description"]["planar_surfaces"][0]["vertices"][0]["x_m"] = -1

    result = codec.from_dict(payload)

    assert result.errors[0].path == (
        "room_description", "planar_surfaces", 0, "vertices", 0, "x_m"
    )
