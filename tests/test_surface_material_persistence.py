import json

import pytest

from acousticbrain.models import (
    RoomDescription,
    RoomDescriptionPersistenceErrorCode,
    RoomDescriptionValidationCode,
    RoomDimensions,
    SurfaceMaterialAssignment,
    SurfaceMaterialCoefficient,
    SurfaceMaterialDescription,
    SurfaceMaterialPrecision,
    SurfaceMaterialQuality,
    SurfaceMaterialSource,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec


def description(reverse=False):
    materials = (
        SurfaceMaterialDescription(
            "absorber", "Absorber",
            absorption_coefficients=(
                SurfaceMaterialCoefficient(125, 0.4),
                SurfaceMaterialCoefficient(250, 0.7),
            ),
            diffusion_coefficients=(SurfaceMaterialCoefficient(125, 0.1),),
            transmission_coefficients=None,
            source=SurfaceMaterialSource.MEASURED,
            confidence=92,
            quality=SurfaceMaterialQuality.VERIFIED,
            precision=SurfaceMaterialPrecision.OCTAVE,
            provenance_codes=("LAB-2026",),
        ),
        SurfaceMaterialDescription(
            "glass", "Glass",
            absorption_coefficients=(), diffusion_coefficients=(),
            transmission_coefficients=(SurfaceMaterialCoefficient(500, 0.6),),
            source=SurfaceMaterialSource.DATABASE,
            confidence=70,
            quality=SurfaceMaterialQuality.ESTIMATED,
            precision=SurfaceMaterialPrecision.BROADBAND,
            provenance_codes=("DB-1", "ENTRY-4"),
        ),
    )
    assignments = (
        SurfaceMaterialAssignment("a-floor", "glass", surface_id="floor"),
        SurfaceMaterialAssignment("a-front", "absorber", surface_id="front_wall"),
    )
    if reverse:
        materials = tuple(reversed(materials))
        assignments = tuple(reversed(assignments))
    return RoomDescription(
        "room", RoomDimensions(5, 4, 3),
        materials=materials, material_assignments=assignments,
    )


def test_schema_v4_round_trip_preserves_material_profiles_and_assignments():
    codec = RoomDescriptionJsonCodec()
    payload = codec.dumps(description())
    result = codec.loads(payload)

    assert result.description == description()
    assert result.source_schema_version == 5
    assert not result.requires_migration
    assert json.loads(payload)["schema_version"] == 5


def test_schema_v4_writer_is_deterministic_by_stable_identifiers():
    codec = RoomDescriptionJsonCodec()
    assert codec.dumps(description()) == codec.dumps(description(reverse=True))


@pytest.mark.parametrize("version", [1, 2, 3])
def test_previous_schemas_migrate_without_inventing_frequency_properties(version):
    codec = RoomDescriptionJsonCodec()
    payload = codec.to_dict(RoomDescription("legacy", RoomDimensions(5, 4, 3)))
    payload["schema_version"] = version
    payload["room_description"].pop("materials")
    payload["room_description"].pop("material_assignments")
    if version < 3:
        payload["room_description"].pop("planar_surfaces")
        payload["room_description"].pop("planar_regions")

    result = codec.from_dict(payload)

    assert result.is_success
    assert result.requires_migration
    assert result.description.materials == ()
    assert result.description.material_assignments == ()


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("materials", 0, "absorption_coefficients", 0, "coefficient"), 1.1),
        (("materials", 0, "confidence"), 101),
        (("materials", 0, "source"), "UNKNOWN"),
        (("material_assignments", 0, "surface_id"), ""),
    ],
)
def test_schema_v4_reports_precise_invalid_value_paths(path, value):
    payload = RoomDescriptionJsonCodec().to_dict(description())
    target = payload["room_description"]
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert result.errors[0].code is RoomDescriptionPersistenceErrorCode.INVALID_VALUE
    assert result.errors[0].path == ("room_description", *path)


def test_unknown_material_assignment_is_rejected_relationally():
    payload = RoomDescriptionJsonCodec().to_dict(description())
    payload["room_description"]["material_assignments"][0]["material_id"] = "missing"

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert result.errors[0].validation_code is (
        RoomDescriptionValidationCode.MATERIAL_ASSIGNMENT_UNKNOWN_MATERIAL
    )


def test_unknown_surface_assignment_is_rejected_relationally():
    payload = RoomDescriptionJsonCodec().to_dict(description())
    payload["room_description"]["material_assignments"][0]["surface_id"] = "unknown"

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert result.errors[0].validation_code is (
        RoomDescriptionValidationCode.MATERIAL_ASSIGNMENT_UNKNOWN_TARGET
    )


def test_duplicate_target_assignments_are_rejected_relationally():
    payload = RoomDescriptionJsonCodec().to_dict(description())
    duplicate = dict(payload["room_description"]["material_assignments"][0])
    duplicate["assignment_id"] = "duplicate"
    payload["room_description"]["material_assignments"].append(duplicate)

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert result.errors[0].validation_code is (
        RoomDescriptionValidationCode.MATERIAL_ASSIGNMENT_DUPLICATE_TARGET
    )
