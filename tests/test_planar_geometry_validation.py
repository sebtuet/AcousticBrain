import pytest

from acousticbrain.models import (
    AcousticTreatmentDescription,
    AcousticTreatmentType,
    PlanarRegionDescription,
    PlanarRegionRole,
    PlanarSurfaceDescription,
    PlanarSurfaceRole,
    PlanarVertexDescription as Vertex,
    RoomDescription,
    RoomDescriptionValidationCode,
    RoomDimensions,
)
from acousticbrain.validation import RoomDescriptionValidator


def surface(vertices=None):
    return PlanarSurfaceDescription(
        "wall",
        PlanarSurfaceRole.LEFT_WALL,
        vertices or (
            Vertex(0.0, 0.0, 0.0),
            Vertex(4.0, 0.5, 0.0),
            Vertex(4.0, 0.5, 2.5),
            Vertex(0.0, 0.0, 2.5),
        ),
    )


def validate(*, surfaces=(), regions=(), treatments=()):
    return RoomDescriptionValidator().validate(RoomDescription(
        "room",
        RoomDimensions(5.0, 4.0, 3.0),
        planar_surfaces=surfaces,
        planar_regions=regions,
        acoustic_treatments=treatments,
    ))


def test_accepts_convex_oblique_surface_and_contained_region():
    wall = surface()
    region = PlanarRegionDescription(
        "panel_region",
        wall.surface_id,
        PlanarRegionRole.TREATMENT,
        (
            Vertex(1.0, 0.125, 0.5),
            Vertex(2.0, 0.25, 0.5),
            Vertex(2.0, 0.25, 1.5),
            Vertex(1.0, 0.125, 1.5),
        ),
        feature_id="panel",
    )
    treatment = AcousticTreatmentDescription(
        "panel", AcousticTreatmentType.ABSORBER
    )

    result = validate(
        surfaces=(wall,), regions=(region,), treatments=(treatment,)
    )

    assert result.is_valid


@pytest.mark.parametrize(
    ("vertices", "code"),
    [
        ((Vertex(0, 0, 0), Vertex(1, 0, 0), Vertex(2, 0, 0)),
         RoomDescriptionValidationCode.PLANAR_SURFACE_INVALID_POLYGON),
        ((Vertex(0, 0, 0), Vertex(2, 0, 0), Vertex(1, 1, 0), Vertex(2, 2, 0), Vertex(0, 2, 0)),
         RoomDescriptionValidationCode.PLANAR_SURFACE_INVALID_POLYGON),
        ((Vertex(0, 0, 0), Vertex(2, 0, 0), Vertex(2, 2, 0), Vertex(0, 2, 0.1)),
         RoomDescriptionValidationCode.PLANAR_SURFACE_INVALID_POLYGON),
    ],
)
def test_rejects_invalid_planar_surface_polygons(vertices, code):
    result = validate(surfaces=(surface(vertices),))
    assert result.errors[0].code is code


def test_rejects_unknown_parent_surface():
    region = PlanarRegionDescription(
        "region", "missing", PlanarRegionRole.OPENING,
        (Vertex(0, 0, 0), Vertex(1, 0, 0), Vertex(1, 1, 0)),
    )
    result = validate(regions=(region,))
    assert result.errors[0].code is RoomDescriptionValidationCode.PLANAR_REGION_UNKNOWN_SURFACE


def test_rejects_non_coplanar_and_outside_regions():
    wall = surface()
    non_coplanar = PlanarRegionDescription(
        "non_coplanar", "wall", PlanarRegionRole.OPENING,
        (Vertex(1, 0.125, 0.5), Vertex(2, 0.25, 0.5), Vertex(2, 0.4, 1.5)),
    )
    outside = PlanarRegionDescription(
        "outside", "wall", PlanarRegionRole.OPENING,
        (Vertex(4, 0.5, 0.5), Vertex(5, 0.625, 0.5), Vertex(5, 0.625, 1.5)),
    )

    result = validate(surfaces=(wall,), regions=(non_coplanar, outside))

    assert [item.code for item in result.errors] == [
        RoomDescriptionValidationCode.PLANAR_REGION_NOT_COPLANAR,
        RoomDescriptionValidationCode.PLANAR_REGION_OUTSIDE_SURFACE,
    ]


def test_rejects_unknown_feature_and_double_placement():
    wall = surface()
    vertices = (Vertex(1, 0.125, 0.5), Vertex(2, 0.25, 0.5), Vertex(2, 0.25, 1.5))
    missing = PlanarRegionDescription(
        "missing", "wall", PlanarRegionRole.TREATMENT, vertices, "unknown"
    )
    conflict = PlanarRegionDescription(
        "conflict", "wall", PlanarRegionRole.TREATMENT, vertices, "placed"
    )
    placed = AcousticTreatmentDescription(
        "placed", AcousticTreatmentType.ABSORBER, surface=None
    )
    object.__setattr__(placed, "horizontal_offset_m", 0.1)

    result = validate(
        surfaces=(wall,), regions=(missing, conflict), treatments=(placed,)
    )

    assert {item.code for item in result.errors} == {
        RoomDescriptionValidationCode.PLANAR_REGION_UNKNOWN_FEATURE,
        RoomDescriptionValidationCode.PLANAR_REGION_PLACEMENT_CONFLICT,
        RoomDescriptionValidationCode.INVALID_FEATURE_PLACEMENT,
    }
