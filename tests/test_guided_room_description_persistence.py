from dataclasses import replace

import pytest

from acousticbrain.catalogs import BuiltInSurfaceMaterialCatalog
from acousticbrain.models import (
    RoomDescription,
    RoomDimensions,
    SurfaceMaterialAssignment,
    SurfaceMaterialDescriptionSource,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec


def described_room():
    material = BuiltInSurfaceMaterialCatalog().get(
        "material.gypsum_board_painted.v1"
    ).material
    return RoomDescription(
        "room", RoomDimensions(5, 4, 3),
        materials=(material,),
        material_assignments=(SurfaceMaterialAssignment(
            "guided:surface:left_wall", material.material_id,
            surface_id="left_wall",
            description_source=(
                SurfaceMaterialDescriptionSource.USER_DESCRIPTION_INTERPRETED
            ),
            description_confidence=60.0,
            provenance_codes=("USER_DESCRIPTION_INTERPRETED",),
        ),),
    )


def test_schema_v5_round_trip_preserves_separate_provenances():
    codec = RoomDescriptionJsonCodec()
    payload = codec.to_dict(described_room())
    result = codec.from_dict(payload)

    assert payload["schema_version"] == 5
    assert result.description == described_room()
    assert result.description.materials[0].catalog_entry_id.endswith(".v1")
    assert result.description.material_assignments[0].description_confidence == 60.0


def test_schema_v4_migrates_additively_without_inventing_provenance():
    codec = RoomDescriptionJsonCodec()
    payload = codec.to_dict(described_room())
    payload["schema_version"] = 4
    material = payload["room_description"]["materials"][0]
    material["source"] = "DATABASE"
    material.pop("catalog_entry_id")
    assignment = payload["room_description"]["material_assignments"][0]
    assignment.pop("description_source")
    assignment.pop("description_confidence")
    assignment.pop("provenance_codes")

    result = codec.from_dict(payload)

    assert result.is_success
    assert result.requires_migration
    assert result.description.materials[0].catalog_entry_id is None
    assert result.description.material_assignments[0].description_source is (
        SurfaceMaterialDescriptionSource.IMPORTED_PROJECT_DATA
    )
    assert result.description.material_assignments[0].description_confidence == 0.0


@pytest.mark.parametrize("version", [1, 2, 3])
def test_legacy_schemas_still_create_no_material_or_conversational_fact(version):
    codec = RoomDescriptionJsonCodec()
    payload = codec.to_dict(RoomDescription("legacy", RoomDimensions(5, 4, 3)))
    payload["schema_version"] = version
    if version < 3:
        payload["room_description"].pop("planar_surfaces")
        payload["room_description"].pop("planar_regions")
    payload["room_description"].pop("materials")
    payload["room_description"].pop("material_assignments")

    result = codec.from_dict(payload)

    assert result.is_success
    assert result.description.materials == ()
    assert result.description.material_assignments == ()


@pytest.mark.parametrize(
    "field,value",
    [
        ("description_source", "LLM_INVENTED"),
        ("description_confidence", 101),
        ("provenance_codes", [""]),
    ],
)
def test_schema_v5_rejects_invalid_assignment_provenance(field, value):
    codec = RoomDescriptionJsonCodec()
    payload = codec.to_dict(described_room())
    payload["room_description"]["material_assignments"][0][field] = value
    result = codec.from_dict(payload)
    assert not result.is_success


def test_writer_never_resolves_catalog_entry_to_a_newer_version():
    codec = RoomDescriptionJsonCodec()
    rewritten = codec.loads(codec.dumps(described_room())).description
    assert rewritten.materials[0].catalog_entry_id == (
        "material.gypsum_board_painted.v1"
    )
