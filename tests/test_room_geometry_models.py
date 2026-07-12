from dataclasses import FrozenInstanceError, fields

import pytest

from acousticbrain.models import (
    GeometryOpening,
    GeometryPoint,
    GeometrySource,
    RoomDimensions,
    RoomGeometry,
    RoomGeometryModel,
    RoomSurface,
    RoomSurfaceKind,
)


def point(point_id="origin", x=0.0, y=0.0, z=0.0):
    return GeometryPoint(point_id=point_id, x_m=x, y_m=y, z_m=z)


def surface(surface_id="front"):
    return RoomSurface(
        surface_id=surface_id,
        kind=RoomSurfaceKind.FRONT_WALL,
        origin=point(f"{surface_id}-origin"),
        width_m=5.0,
        height_m=2.5,
    )


def geometry(**overrides):
    values = {
        "dimensions": RoomDimensions(6.0, 5.0, 2.5),
        "surfaces": (surface(),),
        "speakers": (point("left", 1.0, 1.0, 1.0),),
        "listening_positions": (point("seat", 4.0, 2.5, 1.1),),
        "openings": (
            GeometryOpening("door", "front", 1.0, 0.0, 0.9, 2.1),
        ),
        "source": GeometrySource.ROOM_DESCRIPTION,
        "model": RoomGeometryModel.RECTANGULAR,
        "model_version": 1,
        "completeness": 100.0,
    }
    values.update(overrides)
    return RoomGeometry(**values)


def test_geometry_contract_preserves_explicit_facts_and_provenance():
    result = geometry()

    assert result.dimensions == RoomDimensions(6.0, 5.0, 2.5)
    assert result.source is GeometrySource.ROOM_DESCRIPTION
    assert result.model is RoomGeometryModel.RECTANGULAR
    assert result.model_version == 1
    assert result.completeness == 100.0
    assert result.openings[0].surface_id == "front"


def test_geometry_collections_and_nested_models_are_immutable():
    result = geometry()

    with pytest.raises(FrozenInstanceError):
        result.completeness = 50.0
    with pytest.raises(FrozenInstanceError):
        result.speakers[0].x_m = 2.0
    with pytest.raises(AttributeError):
        result.surfaces.append(surface("rear"))


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: point("", 0.0, 0.0, 0.0), "identifier"),
        (lambda: point("p", float("nan"), 0.0, 0.0), "finite"),
        (lambda: point("p", -0.1, 0.0, 0.0), "negative"),
        (
            lambda: RoomSurface("s", RoomSurfaceKind.FLOOR, point(), 0.0, 2.0),
            "positive",
        ),
        (
            lambda: GeometryOpening("o", "s", 0.0, 0.0, 0.0, 1.0),
            "positive",
        ),
    ],
)
def test_local_geometry_models_reject_invalid_values(factory, message):
    with pytest.raises(ValueError, match=message):
        factory()


@pytest.mark.parametrize(
    "overrides",
    [
        {"surfaces": [surface()]},
        {"source": "ROOM_DESCRIPTION"},
        {"model": "RECTANGULAR"},
        {"model_version": 0},
        {"model_version": True},
        {"completeness": -0.1},
        {"completeness": 100.1},
        {"completeness": float("inf")},
    ],
)
def test_room_geometry_rejects_invalid_contract_values(overrides):
    with pytest.raises(ValueError):
        geometry(**overrides)


@pytest.mark.parametrize(
    "overrides",
    [
        {"surfaces": (surface("same"), surface("same"))},
        {"speakers": (point("same"), point("same"))},
        {"listening_positions": (point("same"), point("same"))},
        {
            "openings": (
                GeometryOpening("same", "front", 0.0, 0.0, 1.0, 1.0),
                GeometryOpening("same", "front", 2.0, 0.0, 1.0, 1.0),
            )
        },
    ],
)
def test_room_geometry_rejects_duplicate_identifiers_by_category(overrides):
    with pytest.raises(ValueError, match="duplicate"):
        geometry(**overrides)


def test_contract_contains_no_acoustic_result_or_ui_field():
    names = {field.name for field in fields(RoomGeometry)}

    assert not names & {
        "volume",
        "surface_area",
        "schroeder_frequency",
        "room_modes",
        "reflection_paths",
        "score",
        "recommendations",
        "widget",
    }


def test_relational_geometry_is_deliberately_deferred_to_builder():
    result = geometry(
        openings=(
            GeometryOpening("unresolved", "unknown", 99.0, 99.0, 1.0, 1.0),
        )
    )

    assert result.openings[0].surface_id == "unknown"
