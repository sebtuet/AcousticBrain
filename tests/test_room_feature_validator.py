import pytest

from acousticbrain.models import (
    AcousticTreatmentDescription,
    AcousticTreatmentType,
    FurnitureType,
    RoomDescription,
    RoomDescriptionEntityType,
    RoomDescriptionSurface,
    RoomDescriptionValidationCode,
    RoomDimensions,
    RoomFurnitureDescription,
    SurfaceCoveringZone,
    SurfaceMaterialType,
)
from acousticbrain.validation import RoomDescriptionValidator


def description(**changes):
    values = {
        "name": "Room",
        "dimensions": RoomDimensions(5.0, 4.0, 2.5),
    }
    values.update(changes)
    return RoomDescription(**values)


def zone(
    zone_id,
    *,
    surface=RoomDescriptionSurface.FLOOR,
    horizontal=0.0,
    vertical=0.0,
    width=1.0,
    height=1.0,
):
    return SurfaceCoveringZone(
        zone_id,
        surface,
        SurfaceMaterialType.CARPET,
        horizontal_offset_m=horizontal,
        vertical_offset_m=vertical,
        width_m=width,
        height_m=height,
    )


def treatment(
    treatment_id,
    *,
    surface=RoomDescriptionSurface.FRONT_WALL,
    horizontal=0.0,
    vertical=0.0,
    width=1.0,
    height=1.0,
):
    return AcousticTreatmentDescription(
        treatment_id,
        AcousticTreatmentType.ABSORBER,
        surface=surface,
        horizontal_offset_m=horizontal,
        vertical_offset_m=vertical,
        width_m=width,
        height_m=height,
    )


def furniture(
    furniture_id,
    *,
    x=0.0,
    y=0.0,
    z=0.0,
    length=1.0,
    width=1.0,
    height=1.0,
):
    return RoomFurnitureDescription(
        furniture_id,
        FurnitureType.OTHER,
        x_m=x,
        y_m=y,
        z_m=z,
        length_m=length,
        width_m=width,
        height_m=height,
    )


@pytest.mark.parametrize(
    ("surface", "horizontal_limit", "vertical_limit"),
    [
        (RoomDescriptionSurface.FRONT_WALL, 4.0, 2.5),
        (RoomDescriptionSurface.REAR_WALL, 4.0, 2.5),
        (RoomDescriptionSurface.LEFT_WALL, 5.0, 2.5),
        (RoomDescriptionSurface.RIGHT_WALL, 5.0, 2.5),
        (RoomDescriptionSurface.FLOOR, 5.0, 4.0),
        (RoomDescriptionSurface.CEILING, 5.0, 4.0),
    ],
)
def test_accepts_covering_zone_on_each_complete_local_surface_boundary(
    surface,
    horizontal_limit,
    vertical_limit,
):
    room = description(
        covering_zones=(
            zone(
                "EDGE",
                surface=surface,
                horizontal=horizontal_limit - 1.0,
                vertical=vertical_limit - 1.0,
            ),
        )
    )

    assert RoomDescriptionValidator().validate(room).is_valid


def test_reports_covering_zone_outside_its_local_surface():
    room = description(
        covering_zones=(
            zone("RUG", horizontal=4.5, vertical=3.5, width=1.0, height=1.0),
        )
    )

    error = RoomDescriptionValidator().validate(room).errors[0]

    assert error.code is RoomDescriptionValidationCode.COVERING_ZONE_OUTSIDE_SURFACE
    assert error.entity_type is RoomDescriptionEntityType.COVERING_ZONE
    assert error.entity_ids == ("RUG",)
    assert error.fields == (
        "horizontal_offset_m",
        "width_m",
        "vertical_offset_m",
        "height_m",
    )


def test_covering_overlap_requires_positive_area_on_the_same_surface():
    overlapping = description(
        covering_zones=(
            zone("B", horizontal=0.5),
            zone("A", horizontal=0.0),
        )
    )
    touching = description(
        covering_zones=(
            zone("A", horizontal=0.0),
            zone("B", horizontal=1.0),
            zone("C", surface=RoomDescriptionSurface.CEILING),
        )
    )

    error = RoomDescriptionValidator().validate(overlapping).errors[0]

    assert error.code is RoomDescriptionValidationCode.COVERING_ZONE_OVERLAP
    assert error.entity_ids == ("A", "B")
    assert RoomDescriptionValidator().validate(touching).is_valid


def test_accepts_unplaced_covering_zone():
    room = description(
        covering_zones=(
            SurfaceCoveringZone(
                "RUG",
                RoomDescriptionSurface.FLOOR,
                SurfaceMaterialType.CARPET,
            ),
        )
    )

    assert RoomDescriptionValidator().validate(room).is_valid


def test_reports_furniture_box_outside_room_volume():
    room = description(
        furniture=(
            furniture("SOFA", x=4.5, y=3.5, z=2.0, length=1.0, width=1.0, height=1.0),
        )
    )

    error = RoomDescriptionValidator().validate(room).errors[0]

    assert error.code is RoomDescriptionValidationCode.FURNITURE_OUTSIDE_ROOM
    assert error.entity_type is RoomDescriptionEntityType.FURNITURE
    assert error.fields == (
        "x_m",
        "length_m",
        "y_m",
        "width_m",
        "z_m",
        "height_m",
    )


def test_furniture_overlap_requires_positive_volume_and_accepts_contacts():
    overlapping = description(
        furniture=(
            furniture("B", x=0.5, y=0.5, z=0.5),
            furniture("A"),
        )
    )
    touching = description(
        furniture=(
            furniture("A"),
            furniture("FACE", x=1.0),
            furniture("EDGE", x=1.0, y=1.0),
            furniture("CORNER", x=1.0, y=1.0, z=1.0),
        )
    )

    error = RoomDescriptionValidator().validate(overlapping).errors[0]

    assert error.code is RoomDescriptionValidationCode.FURNITURE_OVERLAP
    assert error.entity_ids == ("A", "B")
    assert RoomDescriptionValidator().validate(touching).is_valid


def test_accepts_unplaced_furniture():
    room = description(
        furniture=(RoomFurnitureDescription("SOFA", FurnitureType.SOFA),)
    )

    assert RoomDescriptionValidator().validate(room).is_valid


def test_reports_treatment_outside_surface_and_detects_same_surface_overlap():
    outside = description(
        acoustic_treatments=(
            treatment("PANEL", horizontal=3.5, vertical=2.0),
        )
    )
    overlapping = description(
        acoustic_treatments=(
            treatment("B", horizontal=0.5),
            treatment("A"),
        )
    )

    outside_error = RoomDescriptionValidator().validate(outside).errors[0]
    overlap_error = RoomDescriptionValidator().validate(overlapping).errors[0]

    assert outside_error.code is RoomDescriptionValidationCode.TREATMENT_OUTSIDE_SURFACE
    assert outside_error.entity_type is RoomDescriptionEntityType.ACOUSTIC_TREATMENT
    assert overlap_error.code is RoomDescriptionValidationCode.TREATMENT_OVERLAP
    assert overlap_error.entity_ids == ("A", "B")


def test_treatments_accept_edge_contact_and_different_surfaces():
    room = description(
        acoustic_treatments=(
            treatment("A"),
            treatment("EDGE", horizontal=1.0),
            treatment("OTHER", surface=RoomDescriptionSurface.REAR_WALL),
        )
    )

    assert RoomDescriptionValidator().validate(room).is_valid


def test_cross_category_overlap_is_explicitly_allowed_for_rug_under_sofa():
    room = description(
        covering_zones=(zone("RUG", horizontal=0.0, vertical=0.0, width=3.0, height=3.0),),
        furniture=(furniture("SOFA", x=1.0, y=1.0, z=0.0),),
    )

    assert RoomDescriptionValidator().validate(room).is_valid


def test_cross_category_surface_overlap_is_not_compared():
    room = description(
        covering_zones=(
            zone("FABRIC", surface=RoomDescriptionSurface.FRONT_WALL),
        ),
        acoustic_treatments=(treatment("PANEL"),),
    )

    assert RoomDescriptionValidator().validate(room).is_valid


@pytest.mark.parametrize(
    ("collection_name", "feature", "entity_type"),
    [
        (
            "covering_zones",
            zone("ZONE"),
            RoomDescriptionEntityType.COVERING_ZONE,
        ),
        (
            "furniture",
            furniture("ITEM"),
            RoomDescriptionEntityType.FURNITURE,
        ),
        (
            "acoustic_treatments",
            treatment("PANEL"),
            RoomDescriptionEntityType.ACOUSTIC_TREATMENT,
        ),
    ],
)
def test_defensively_reports_corrupted_partial_placement(
    collection_name,
    feature,
    entity_type,
):
    field = (
        "horizontal_offset_m"
        if collection_name != "furniture"
        else "x_m"
    )
    object.__setattr__(feature, field, None)
    room = description(**{collection_name: (feature,)})

    error = RoomDescriptionValidator().validate(room).errors[0]

    assert error.code is RoomDescriptionValidationCode.INVALID_FEATURE_PLACEMENT
    assert error.entity_type is entity_type
    assert error.entity_ids == (
        getattr(feature, "zone_id", None)
        or getattr(feature, "furniture_id", None)
        or getattr(feature, "treatment_id"),
    )


def test_overlap_pairs_and_feature_categories_are_ordered_deterministically():
    room = description(
        covering_zones=(
            zone("C", horizontal=0.2),
            zone("A"),
            zone("B", horizontal=0.1),
        ),
        furniture=(
            furniture("C", x=0.2),
            furniture("A"),
            furniture("B", x=0.1),
        ),
        acoustic_treatments=(
            treatment("C", horizontal=0.2),
            treatment("A"),
            treatment("B", horizontal=0.1),
        ),
    )

    result = RoomDescriptionValidator().validate(room)

    assert [(error.code, error.entity_ids) for error in result.errors] == [
        (RoomDescriptionValidationCode.COVERING_ZONE_OVERLAP, ("A", "B")),
        (RoomDescriptionValidationCode.COVERING_ZONE_OVERLAP, ("A", "C")),
        (RoomDescriptionValidationCode.COVERING_ZONE_OVERLAP, ("B", "C")),
        (RoomDescriptionValidationCode.FURNITURE_OVERLAP, ("A", "B")),
        (RoomDescriptionValidationCode.FURNITURE_OVERLAP, ("A", "C")),
        (RoomDescriptionValidationCode.FURNITURE_OVERLAP, ("B", "C")),
        (RoomDescriptionValidationCode.TREATMENT_OVERLAP, ("A", "B")),
        (RoomDescriptionValidationCode.TREATMENT_OVERLAP, ("A", "C")),
        (RoomDescriptionValidationCode.TREATMENT_OVERLAP, ("B", "C")),
    ]
