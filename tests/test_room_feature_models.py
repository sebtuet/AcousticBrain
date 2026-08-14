from dataclasses import FrozenInstanceError, fields

import pytest

from acousticbrain.models import (
    AcousticTreatmentDescription,
    AcousticTreatmentType,
    FurnitureType,
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


def test_old_speaker_position_calls_remain_compatible():
    speaker = SpeakerPosition("LEFT", 0.54, 0.77, 0.88)

    assert speaker.orientation is None


def test_reference_speaker_orientations_preserve_signed_toe_in():
    left = SpeakerPosition(
        "LEFT",
        0.54,
        0.77,
        0.88,
        SpeakerOrientation(+15.0),
    )
    right = SpeakerPosition(
        "RIGHT",
        0.51,
        3.25,
        0.88,
        SpeakerOrientation(-15.0),
    )

    assert left.orientation.yaw_degrees == 15.0
    assert right.orientation.yaw_degrees == -15.0


@pytest.mark.parametrize("yaw", [float("nan"), float("inf"), -180.1, 180.1, True])
def test_orientation_rejects_invalid_yaw(yaw):
    with pytest.raises(ValueError):
        SpeakerOrientation(yaw)


def test_materials_describe_types_without_acoustic_coefficients():
    ceiling = SurfaceMaterialDescription(
        RoomDescriptionSurface.CEILING,
        SurfaceMaterialType.ACOUSTIC_ASSEMBLY,
        detail="molleton",
    )

    assert ceiling.detail == "molleton"
    assert not {field.name for field in fields(ceiling)} & {
        "absorption",
        "absorption_coefficient",
        "diffusion",
        "diffusion_coefficient",
        "transmission_loss",
    }


def test_optional_material_detail_stays_none():
    material = SurfaceMaterialDescription(
        RoomDescriptionSurface.FRONT_WALL,
        SurfaceMaterialType.WOOD,
    )

    assert material.detail is None


def test_rug_can_be_declared_before_its_local_surface_placement_is_known():
    rug = SurfaceCoveringZone(
        zone_id="rug",
        surface=RoomDescriptionSurface.FLOOR,
        material_type=SurfaceMaterialType.CARPET,
    )

    assert rug.horizontal_offset_m is None
    assert rug.vertical_offset_m is None
    assert rug.width_m is None
    assert rug.height_m is None


def test_covering_offsets_use_a_complete_local_surface_rectangle():
    rug = SurfaceCoveringZone(
        zone_id="rug",
        surface=RoomDescriptionSurface.FLOOR,
        material_type=SurfaceMaterialType.CARPET,
        horizontal_offset_m=1.0,
        vertical_offset_m=0.5,
        width_m=3.0,
        height_m=2.0,
    )

    assert (
        rug.horizontal_offset_m,
        rug.vertical_offset_m,
        rug.width_m,
        rug.height_m,
    ) == (1.0, 0.5, 3.0, 2.0)


@pytest.mark.parametrize(
    "values",
    [
        (0.0, None, 1.0, 1.0),
        (-0.1, 0.0, 1.0, 1.0),
        (0.0, 0.0, 0.0, 1.0),
        (0.0, 0.0, float("nan"), 1.0),
        (False, 0.0, 1.0, 1.0),
    ],
)
def test_covering_zone_rejects_partial_or_invalid_placement(values):
    with pytest.raises(ValueError):
        SurfaceCoveringZone(
            "rug",
            RoomDescriptionSurface.FLOOR,
            SurfaceMaterialType.CARPET,
            horizontal_offset_m=values[0],
            vertical_offset_m=values[1],
            width_m=values[2],
            height_m=values[3],
        )


def test_furniture_can_be_known_without_a_bounding_box():
    sofa = RoomFurnitureDescription("sofa", FurnitureType.SOFA)

    assert sofa.x_m is None
    assert sofa.length_m is None


def test_furniture_position_is_the_minimum_corner_of_a_complete_box():
    sofa = RoomFurnitureDescription(
        "sofa",
        FurnitureType.SOFA,
        x_m=3.5,
        y_m=1.0,
        z_m=0.0,
        length_m=1.0,
        width_m=2.5,
        height_m=0.9,
    )

    assert (sofa.x_m, sofa.y_m, sofa.z_m) == (3.5, 1.0, 0.0)
    assert (sofa.length_m, sofa.width_m, sofa.height_m) == (1.0, 2.5, 0.9)


@pytest.mark.parametrize(
    "overrides",
    [
        {"x_m": 0.0},
        {
            "x_m": -0.1,
            "y_m": 0.0,
            "z_m": 0.0,
            "length_m": 1.0,
            "width_m": 1.0,
            "height_m": 1.0,
        },
        {
            "x_m": 0.0,
            "y_m": 0.0,
            "z_m": 0.0,
            "length_m": 1.0,
            "width_m": 0.0,
            "height_m": 1.0,
        },
    ],
)
def test_furniture_rejects_partial_or_invalid_bounding_box(overrides):
    with pytest.raises(ValueError):
        RoomFurnitureDescription("sofa", FurnitureType.SOFA, **overrides)


def test_treatment_can_be_declared_without_placement():
    treatment = AcousticTreatmentDescription(
        "cloud",
        AcousticTreatmentType.CEILING_CLOUD,
    )

    assert treatment.surface is None
    assert treatment.horizontal_offset_m is None


def test_treatment_accepts_a_complete_surface_local_rectangle():
    treatment = AcousticTreatmentDescription(
        "cloud",
        AcousticTreatmentType.CEILING_CLOUD,
        surface=RoomDescriptionSurface.CEILING,
        horizontal_offset_m=1.0,
        vertical_offset_m=1.0,
        width_m=2.0,
        height_m=1.5,
    )

    assert treatment.surface is RoomDescriptionSurface.CEILING


@pytest.mark.parametrize(
    "kwargs",
    [
        {"surface": RoomDescriptionSurface.CEILING},
        {"horizontal_offset_m": 0.0, "vertical_offset_m": 0.0, "width_m": 1.0, "height_m": 1.0},
        {
            "surface": RoomDescriptionSurface.CEILING,
            "horizontal_offset_m": 0.0,
            "vertical_offset_m": 0.0,
            "width_m": -1.0,
            "height_m": 1.0,
        },
    ],
)
def test_treatment_rejects_partial_or_invalid_surface_placement(kwargs):
    with pytest.raises(ValueError):
        AcousticTreatmentDescription(
            "cloud",
            AcousticTreatmentType.CEILING_CLOUD,
            **kwargs,
        )


def test_minimal_room_description_keeps_all_new_collections_empty():
    description = RoomDescription("Room", RoomDimensions(5.84, 5.51, 2.60))

    assert description.surface_materials == ()
    assert description.covering_zones == ()
    assert description.furniture == ()
    assert description.acoustic_treatments == ()


def test_enriched_room_description_is_immutable_and_preserves_none():
    rug = SurfaceCoveringZone(
        "rug",
        RoomDescriptionSurface.FLOOR,
        SurfaceMaterialType.CARPET,
    )
    description = RoomDescription(
        "Room",
        RoomDimensions(5.84, 5.51, 2.60),
        covering_zones=(rug,),
        furniture=(RoomFurnitureDescription("sofa", FurnitureType.SOFA),),
    )

    with pytest.raises(FrozenInstanceError):
        description.covering_zones = ()
    with pytest.raises(FrozenInstanceError):
        rug.width_m = 2.0
    with pytest.raises(AttributeError):
        description.furniture.append(RoomFurnitureDescription("table", FurnitureType.TABLE))
    assert description.covering_zones[0].width_m is None


@pytest.mark.parametrize(
    "field_values",
    [
        {
            "surface_materials": (
                SurfaceMaterialDescription(RoomDescriptionSurface.FLOOR, SurfaceMaterialType.TILE),
                SurfaceMaterialDescription(RoomDescriptionSurface.FLOOR, SurfaceMaterialType.CARPET),
            )
        },
        {
            "covering_zones": (
                SurfaceCoveringZone("same", RoomDescriptionSurface.FLOOR, SurfaceMaterialType.CARPET),
                SurfaceCoveringZone("same", RoomDescriptionSurface.FLOOR, SurfaceMaterialType.CARPET),
            )
        },
        {
            "furniture": (
                RoomFurnitureDescription("same", FurnitureType.SOFA),
                RoomFurnitureDescription("same", FurnitureType.TABLE),
            )
        },
        {
            "acoustic_treatments": (
                AcousticTreatmentDescription("same", AcousticTreatmentType.ABSORBER),
                AcousticTreatmentDescription("same", AcousticTreatmentType.DIFFUSER),
            )
        },
    ],
)
def test_room_description_rejects_duplicate_feature_identifiers(field_values):
    with pytest.raises(ValueError, match="duplicate"):
        RoomDescription(
            "Room",
            RoomDimensions(5.84, 5.51, 2.60),
            **field_values,
        )


def test_enum_values_are_stable():
    assert tuple(item.value for item in RoomDescriptionSurface) == (
        "FRONT_WALL",
        "REAR_WALL",
        "LEFT_WALL",
        "RIGHT_WALL",
        "FLOOR",
        "CEILING",
    )
    assert SurfaceMaterialType.WOOD.value == "WOOD"
    assert FurnitureType.SOFA.value == "SOFA"
    assert AcousticTreatmentType.ABSORBER.value == "ABSORBER"
