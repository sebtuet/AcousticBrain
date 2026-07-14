import pytest

from acousticbrain.models import (
    RoomDescription,
    RoomDescriptionSurface,
    RoomDimensions,
    SurfaceMaterialAssignment,
    SurfaceMaterialCoefficient,
    SurfaceMaterialDescription,
    SurfaceMaterialPrecision,
    SurfaceMaterialQuality,
    SurfaceMaterialSource,
    SurfaceMaterialType,
)


def coefficient(frequency=125.0, value=0.3):
    return SurfaceMaterialCoefficient(frequency, value)


def material(**overrides):
    values = dict(
        material_id="panel",
        display_name="Broadband panel",
        absorption_coefficients=(coefficient(),),
        diffusion_coefficients=(coefficient(value=0.1),),
        source=SurfaceMaterialSource.MANUFACTURER,
        confidence=85.0,
        quality=SurfaceMaterialQuality.DECLARED,
        precision=SurfaceMaterialPrecision.OCTAVE,
        provenance_codes=("DATASHEET-1",),
    )
    values.update(overrides)
    return SurfaceMaterialDescription(**values)


def test_material_profile_is_immutable_and_preserves_metadata():
    item = material(transmission_coefficients=(coefficient(value=0.05),))

    assert item.material_id == "panel"
    assert item.source is SurfaceMaterialSource.MANUFACTURER
    assert item.transmission_coefficients[0].coefficient == 0.05
    assert not item.is_legacy
    with pytest.raises(AttributeError):
        item.confidence = 10.0


@pytest.mark.parametrize("frequency", [0.0, -1.0, float("inf"), float("nan"), True])
def test_coefficient_rejects_invalid_frequencies(frequency):
    with pytest.raises(ValueError):
        coefficient(frequency=frequency)


@pytest.mark.parametrize("value", [-0.1, 1.1, float("inf"), float("nan"), True, "0.2"])
def test_coefficient_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        coefficient(value=value)


@pytest.mark.parametrize(
    "overrides",
    [
        {"material_id": ""},
        {"display_name": ""},
        {"absorption_coefficients": []},
        {"diffusion_coefficients": [coefficient()]},
        {"transmission_coefficients": []},
    ],
)
def test_material_rejects_invalid_identity_or_coefficient_collections(overrides):
    with pytest.raises(ValueError):
        material(**overrides)


@pytest.mark.parametrize(
    "coefficients",
    [
        (coefficient(250), coefficient(125)),
        (coefficient(125), coefficient(125)),
    ],
)
def test_material_requires_sorted_unique_frequency_bands(coefficients):
    with pytest.raises(ValueError):
        material(absorption_coefficients=coefficients)


@pytest.mark.parametrize(
    "overrides",
    [
        {"confidence": -1},
        {"confidence": 101},
        {"source": "MEASURED"},
        {"quality": "VERIFIED"},
        {"precision": "OCTAVE"},
        {"provenance_codes": ["X"]},
        {"provenance_codes": ("X", "X")},
    ],
)
def test_material_rejects_invalid_quality_metadata(overrides):
    with pytest.raises(ValueError):
        material(**overrides)


@pytest.mark.parametrize(
    "assignment",
    [
        SurfaceMaterialAssignment("wall-panel", "panel", surface_id="front_wall"),
        SurfaceMaterialAssignment("region-panel", "panel", region_id="panel-region"),
    ],
)
def test_assignment_targets_exactly_one_geometry_object(assignment):
    assert assignment.target_id
    assert assignment.target_kind in {"SURFACE", "REGION"}


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"surface_id": "wall", "region_id": "region"},
        {"surface_id": ""},
        {"region_id": ""},
    ],
)
def test_assignment_rejects_missing_ambiguous_or_empty_targets(kwargs):
    with pytest.raises(ValueError):
        SurfaceMaterialAssignment("assignment", "panel", **kwargs)


def test_legacy_constructor_remains_available_without_frequency_facts():
    legacy = SurfaceMaterialDescription(
        RoomDescriptionSurface.FRONT_WALL,
        SurfaceMaterialType.WOOD,
        "oak",
    )

    assert legacy.is_legacy
    assert legacy.surface is RoomDescriptionSurface.FRONT_WALL
    assert legacy.material_type is SurfaceMaterialType.WOOD
    assert legacy.absorption_coefficients == ()


def test_room_description_keeps_catalog_and_assignments_separate():
    description = RoomDescription(
        "room",
        RoomDimensions(5, 4, 3),
        materials=(material(),),
        material_assignments=(
            SurfaceMaterialAssignment("front", "panel", surface_id="front_wall"),
        ),
    )

    assert description.surface_materials == ()
    assert description.materials[0].material_id == "panel"


@pytest.mark.parametrize("field", ["materials", "material_assignments"])
def test_room_description_rejects_duplicate_material_identifiers(field):
    kwargs = {
        "materials": (material(), material()),
    } if field == "materials" else {
        "material_assignments": (
            SurfaceMaterialAssignment("same", "a", surface_id="front_wall"),
            SurfaceMaterialAssignment("same", "b", surface_id="rear_wall"),
        )
    }
    with pytest.raises(ValueError):
        RoomDescription("room", RoomDimensions(5, 4, 3), **kwargs)
