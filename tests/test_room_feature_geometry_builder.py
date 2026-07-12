from dataclasses import fields

import pytest

from acousticbrain.analysis import RoomGeometryBuildException, RoomGeometryBuilder
from acousticbrain.models import (
    AcousticTreatmentDescription,
    AcousticTreatmentType,
    FurnitureType,
    GeometryAcousticTreatment,
    GeometryAcousticTreatmentType,
    GeometryCoveringZone,
    GeometryFurniture,
    GeometryFurnitureType,
    GeometryMaterialType,
    GeometrySource,
    GeometrySurfaceMaterial,
    Room,
    RoomDescription,
    RoomDescriptionSurface,
    RoomDimensions,
    RoomFurnitureDescription,
    SpeakerOrientation,
    SpeakerPosition,
    SurfaceCoveringZone,
    SurfaceMaterialDescription,
    SurfaceMaterialType,
)


def rectangle_feature(surface, *, treatment=False):
    values = {
        "surface": surface,
        "horizontal_offset_m": 0.5,
        "vertical_offset_m": 0.4,
        "width_m": 1.0,
        "height_m": 0.8,
    }
    if treatment:
        return AcousticTreatmentDescription(
            f"treatment-{surface.value}",
            AcousticTreatmentType.ABSORBER,
            **values,
        )
    return SurfaceCoveringZone(
        f"zone-{surface.value}",
        surface,
        SurfaceMaterialType.FABRIC,
        horizontal_offset_m=values["horizontal_offset_m"],
        vertical_offset_m=values["vertical_offset_m"],
        width_m=values["width_m"],
        height_m=values["height_m"],
    )


def enriched_description():
    return RoomDescription(
        "Reference",
        RoomDimensions(5.0, 4.0, 2.5),
        speakers=(
            SpeakerPosition("LEFT", 1.0, 1.0, 1.0, SpeakerOrientation(15.0)),
            SpeakerPosition("RIGHT", 1.0, 3.0, 1.0, SpeakerOrientation(-15.0)),
        ),
        surface_materials=tuple(
            SurfaceMaterialDescription(surface, material)
            for surface, material in (
                (RoomDescriptionSurface.FRONT_WALL, SurfaceMaterialType.WOOD),
                (RoomDescriptionSurface.REAR_WALL, SurfaceMaterialType.CONCRETE),
                (RoomDescriptionSurface.LEFT_WALL, SurfaceMaterialType.CONCRETE),
                (RoomDescriptionSurface.RIGHT_WALL, SurfaceMaterialType.CONCRETE),
                (RoomDescriptionSurface.FLOOR, SurfaceMaterialType.TILE),
                (
                    RoomDescriptionSurface.CEILING,
                    SurfaceMaterialType.ACOUSTIC_ASSEMBLY,
                ),
            )
        ),
        covering_zones=(
            SurfaceCoveringZone(
                "RUG",
                RoomDescriptionSurface.FLOOR,
                SurfaceMaterialType.CARPET,
            ),
            rectangle_feature(RoomDescriptionSurface.REAR_WALL),
        ),
        furniture=(
            RoomFurnitureDescription("SOFA", FurnitureType.SOFA),
            RoomFurnitureDescription(
                "TABLE",
                FurnitureType.TABLE,
                x_m=3.0,
                y_m=1.0,
                z_m=0.0,
                length_m=1.0,
                width_m=1.5,
                height_m=0.6,
            ),
        ),
        acoustic_treatments=(
            AcousticTreatmentDescription(
                "CLOUD", AcousticTreatmentType.CEILING_CLOUD
            ),
            rectangle_feature(RoomDescriptionSurface.FRONT_WALL, treatment=True),
        ),
    )


def test_builder_converts_features_to_distinct_calculable_types():
    result = RoomGeometryBuilder().from_description(enriched_description())

    assert result.source is GeometrySource.ROOM_DESCRIPTION
    assert all(
        isinstance(item, GeometrySurfaceMaterial)
        for item in result.surface_materials
    )
    assert all(isinstance(item, GeometryCoveringZone) for item in result.covering_zones)
    assert all(isinstance(item, GeometryFurniture) for item in result.furniture)
    assert all(
        isinstance(item, GeometryAcousticTreatment)
        for item in result.acoustic_treatments
    )
    assert result.surface_materials[0].material_type is GeometryMaterialType.ACOUSTIC_ASSEMBLY
    assert result.furniture[0].furniture_type is GeometryFurnitureType.SOFA
    assert result.acoustic_treatments[0].treatment_type is (
        GeometryAcousticTreatmentType.CEILING_CLOUD
    )
    assert not isinstance(result.surface_materials[0], SurfaceMaterialDescription)


def test_builder_preserves_orientation_values_and_explicit_none():
    source = RoomDescription(
        "Room",
        RoomDimensions(5.0, 4.0, 2.5),
        speakers=(
            SpeakerPosition("LEFT", 1.0, 1.0, 1.0, SpeakerOrientation(15.0)),
            SpeakerPosition("RIGHT", 1.0, 3.0, 1.0),
        ),
    )

    result = RoomGeometryBuilder().from_description(source)

    assert [(item.speaker_id, item.yaw_degrees) for item in result.speaker_orientations] == [
        ("LEFT", 15.0),
        ("RIGHT", None),
    ]


@pytest.mark.parametrize(
    ("surface", "minimum", "maximum"),
    [
        (RoomDescriptionSurface.FRONT_WALL, (0.0, 0.5, 0.4), (0.0, 1.5, 1.2)),
        (RoomDescriptionSurface.REAR_WALL, (5.0, 0.5, 0.4), (5.0, 1.5, 1.2)),
        (RoomDescriptionSurface.LEFT_WALL, (0.5, 0.0, 0.4), (1.5, 0.0, 1.2)),
        (RoomDescriptionSurface.RIGHT_WALL, (0.5, 4.0, 0.4), (1.5, 4.0, 1.2)),
        (RoomDescriptionSurface.FLOOR, (0.5, 0.4, 0.0), (1.5, 1.2, 0.0)),
        (RoomDescriptionSurface.CEILING, (0.5, 0.4, 2.5), (1.5, 1.2, 2.5)),
    ],
)
def test_builder_explicitly_converts_each_local_surface_frame(
    surface,
    minimum,
    maximum,
):
    source = RoomDescription(
        "Room",
        RoomDimensions(5.0, 4.0, 2.5),
        covering_zones=(rectangle_feature(surface),),
    )

    placement = RoomGeometryBuilder().from_description(source).covering_zones[0].placement

    assert (
        placement.minimum_corner.x_m,
        placement.minimum_corner.y_m,
        placement.minimum_corner.z_m,
    ) == minimum
    assert (
        placement.maximum_corner.x_m,
        placement.maximum_corner.y_m,
        placement.maximum_corner.z_m,
    ) == pytest.approx(maximum)
    assert (
        placement.horizontal_offset_m,
        placement.vertical_offset_m,
        placement.width_m,
        placement.height_m,
    ) == (0.5, 0.4, 1.0, 0.8)


def test_unplaced_features_remain_present_with_none_placements():
    result = RoomGeometryBuilder().from_description(enriched_description())

    assert result.covering_zones[0].zone_id == "RUG"
    assert result.covering_zones[0].placement is None
    assert result.furniture[0].furniture_id == "SOFA"
    assert result.furniture[0].bounding_box is None
    assert result.acoustic_treatments[0].treatment_id == "CLOUD"
    assert result.acoustic_treatments[0].surface_id is None
    assert result.acoustic_treatments[0].placement is None


def test_furniture_box_uses_declared_minimum_corner_and_derived_maximum():
    result = RoomGeometryBuilder().from_description(enriched_description())
    box = result.furniture[1].bounding_box

    assert (box.minimum_corner.x_m, box.minimum_corner.y_m, box.minimum_corner.z_m) == (
        3.0,
        1.0,
        0.0,
    )
    assert (box.maximum_corner.x_m, box.maximum_corner.y_m, box.maximum_corner.z_m) == (
        4.0,
        2.5,
        0.6,
    )


def test_feature_completeness_is_separate_from_base_geometry_completeness():
    result = RoomGeometryBuilder().from_description(enriched_description())
    feature = result.feature_completeness

    assert result.completeness == 80.0
    assert feature.orientation_coverage == 100.0
    assert feature.material_coverage == 100.0
    assert feature.covering_placement_coverage == 50.0
    assert feature.furniture_placement_coverage == 50.0
    assert feature.treatment_placement_coverage == 50.0
    assert feature.score == 70.0


def test_absent_optional_features_do_not_reduce_or_create_feature_completeness():
    source = RoomDescription("Room", RoomDimensions(5.0, 4.0, 2.5))

    result = RoomGeometryBuilder().from_description(source)

    assert result.completeness == 60.0
    assert result.feature_completeness is None
    assert result.surface_materials == ()
    assert result.covering_zones == ()
    assert result.furniture == ()
    assert result.acoustic_treatments == ()


def test_legacy_geometry_keeps_existing_core_and_no_feature_facts():
    result = RoomGeometryBuilder().from_legacy_room(Room("Legacy", 5.0, 4.0, 2.5))

    assert result.completeness == 60.0
    assert result.feature_completeness is None
    assert result.speaker_orientations == ()
    assert result.surface_materials == ()


def test_relationally_invalid_features_are_rejected_before_conversion():
    source = RoomDescription(
        "Invalid",
        RoomDimensions(5.0, 4.0, 2.5),
        covering_zones=(
            rectangle_feature(RoomDescriptionSurface.FLOOR),
            SurfaceCoveringZone(
                "overlap",
                RoomDescriptionSurface.FLOOR,
                SurfaceMaterialType.CARPET,
                horizontal_offset_m=0.6,
                vertical_offset_m=0.5,
                width_m=1.0,
                height_m=1.0,
            ),
        ),
    )

    with pytest.raises(RoomGeometryBuildException):
        RoomGeometryBuilder().from_description(source)


def test_calculable_feature_models_have_no_acoustic_coefficients():
    names = {
        field.name
        for model in (
            GeometrySurfaceMaterial,
            GeometryCoveringZone,
            GeometryFurniture,
            GeometryAcousticTreatment,
        )
        for field in fields(model)
    }

    assert not names & {
        "absorption_coefficient",
        "diffusion_coefficient",
        "transmission_loss",
        "reflection_coefficient",
    }
