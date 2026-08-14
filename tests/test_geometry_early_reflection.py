import pytest

from acousticbrain.analysis import (
    GeometryEarlyReflectionEngine,
    RoomGeometryBuilder,
)
from acousticbrain.models import (
    GeometryDatumQualityDescription,
    GeometrySource,
    FurnitureType,
    ListeningPosition,
    Room,
    RoomDescription,
    RoomDescriptionSurface,
    RoomDimensions,
    RoomFurnitureDescription,
    SpeakerPosition,
    SurfaceCoveringZone,
    SurfaceMaterialType,
)


def described_geometry(*, include_panel=True, obstruct_front_path=False):
    panel = (
        SurfaceCoveringZone(
            "LEFT_SIDE_WALL_PANEL_02",
            RoomDescriptionSurface.FRONT_WALL,
            SurfaceMaterialType.FABRIC,
            horizontal_offset_m=0.5,
            vertical_offset_m=0.5,
            width_m=1.0,
            height_m=1.0,
        ),
    ) if include_panel else ()
    quality_ids = ("LEFT", "MIC", "front_wall") + (
        ("LEFT_SIDE_WALL_PANEL_02",) if include_panel else ()
    )
    description = RoomDescription(
        "Geometry reference",
        RoomDimensions(5.0, 4.0, 3.0),
        speakers=(SpeakerPosition("LEFT", 1.0, 1.0, 1.0),),
        listening_positions=(ListeningPosition("MIC", 3.0, 1.0, 1.0),),
        covering_zones=panel,
        furniture=(
            RoomFurnitureDescription(
                "OBSTACLE",
                FurnitureType.OTHER,
                x_m=0.4,
                y_m=0.9,
                z_m=0.9,
                length_m=0.2,
                width_m=0.2,
                height_m=0.2,
            ),
        ) if obstruct_front_path else (),
        geometry_data_quality=tuple(
            GeometryDatumQualityDescription(
                datum_id,
                precision_m=0.01,
                confidence=88.0,
                provenance_codes=("LASER_MEASURED",),
            )
            for datum_id in quality_ids
        ),
    )
    return RoomGeometryBuilder().from_description(description)


def test_derives_named_first_order_path_with_uncertainty_and_provenance():
    result = GeometryEarlyReflectionEngine().analyze(described_geometry())

    path = next(
        item for item in result.paths
        if item.base_surface_id == "front_wall"
    )

    assert path.surface_id == "LEFT_SIDE_WALL_PANEL_02"
    assert path.impact_point.x_m == 0.0
    assert path.impact_point.y_m == pytest.approx(1.0)
    assert path.impact_point.z_m == pytest.approx(1.0)
    assert path.direct_path_m == pytest.approx(2.0)
    assert path.reflected_path_m == pytest.approx(4.0)
    assert path.theoretical_delay_ms == pytest.approx(2.0 / 343.0 * 1000.0)
    assert path.uncertainty_ms == pytest.approx(0.08 / 343.0 * 1000.0)
    assert path.confidence == 88.0
    assert path.provenance_codes == ("LASER_MEASURED",)


def test_keeps_base_surface_when_no_named_region_contains_impact():
    result = GeometryEarlyReflectionEngine().analyze(
        described_geometry(include_panel=False)
    )

    front = next(
        item for item in result.paths
        if item.base_surface_id == "front_wall"
    )

    assert front.surface_id == "front_wall"
    assert front.confidence == 88.0


def test_does_not_infer_paths_from_legacy_room_context():
    geometry = RoomGeometryBuilder().from_legacy_room(
        Room("Legacy", 5.0, 4.0, 3.0)
    )

    result = GeometryEarlyReflectionEngine().analyze(geometry)

    assert geometry.source is GeometrySource.LEGACY_ROOM
    assert result.paths == ()


def test_excludes_path_blocked_by_a_placed_obstacle():
    result = GeometryEarlyReflectionEngine().analyze(
        described_geometry(obstruct_front_path=True)
    )

    assert all(
        item.base_surface_id != "front_wall" for item in result.paths
    )
