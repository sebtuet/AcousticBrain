import json

import pytest

from acousticbrain.models import (
    AcousticTreatmentDescription,
    AcousticTreatmentType,
    FurnitureType,
    ListeningPosition,
    RoomDescription,
    RoomDescriptionPersistenceErrorCode,
    RoomDescriptionSurface,
    RoomDescriptionValidationCode,
    RoomDimensions,
    RoomFurnitureDescription,
    SpeakerOrientation,
    SpeakerPosition,
    SurfaceCoveringZone,
    SurfaceMaterialDescription,
    SurfaceMaterialType,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec


def enriched_description(*, reverse=False):
    speakers = (
        SpeakerPosition("LEFT", 0.54, 0.77, 0.88, SpeakerOrientation(15.0)),
        SpeakerPosition("RIGHT", 0.51, 3.25, 0.88, SpeakerOrientation(-15.0)),
    )
    materials = (
        SurfaceMaterialDescription(
            RoomDescriptionSurface.CEILING,
            SurfaceMaterialType.ACOUSTIC_ASSEMBLY,
            detail="molleton",
        ),
        SurfaceMaterialDescription(
            RoomDescriptionSurface.FLOOR,
            SurfaceMaterialType.TILE,
            detail="carrelage",
        ),
        SurfaceMaterialDescription(
            RoomDescriptionSurface.FRONT_WALL,
            SurfaceMaterialType.WOOD,
        ),
    )
    zones = (
        SurfaceCoveringZone(
            "RUG",
            RoomDescriptionSurface.FLOOR,
            SurfaceMaterialType.CARPET,
        ),
        SurfaceCoveringZone(
            "WALL_FABRIC",
            RoomDescriptionSurface.REAR_WALL,
            SurfaceMaterialType.FABRIC,
            horizontal_offset_m=1.0,
            vertical_offset_m=0.5,
            width_m=1.0,
            height_m=1.0,
        ),
    )
    furniture = (
        RoomFurnitureDescription("SOFA", FurnitureType.SOFA),
        RoomFurnitureDescription(
            "TABLE",
            FurnitureType.TABLE,
            x_m=3.5,
            y_m=0.5,
            z_m=0.0,
            length_m=0.8,
            width_m=1.0,
            height_m=0.5,
        ),
    )
    treatments = (
        AcousticTreatmentDescription(
            "CLOUD",
            AcousticTreatmentType.CEILING_CLOUD,
        ),
        AcousticTreatmentDescription(
            "PANEL",
            AcousticTreatmentType.ABSORBER,
            detail="broadband",
            surface=RoomDescriptionSurface.FRONT_WALL,
            horizontal_offset_m=1.0,
            vertical_offset_m=1.0,
            width_m=1.0,
            height_m=1.0,
        ),
    )
    if reverse:
        speakers = tuple(reversed(speakers))
        materials = tuple(reversed(materials))
        zones = tuple(reversed(zones))
        furniture = tuple(reversed(furniture))
        treatments = tuple(reversed(treatments))
    return RoomDescription(
        name="Reference",
        dimensions=RoomDimensions(5.84, 5.51, 2.60),
        speakers=speakers,
        listening_positions=(ListeningPosition("MAIN", 3.0, 2.0, 0.85),),
        surface_materials=materials,
        covering_zones=zones,
        furniture=furniture,
        acoustic_treatments=treatments,
    )


def v1_payload():
    payload = RoomDescriptionJsonCodec().to_dict(
        RoomDescription(
            "Legacy",
            RoomDimensions(5.0, 4.0, 2.5),
            speakers=(SpeakerPosition("LEFT", 1.0, 1.0, 1.0),),
        )
    )
    payload["schema_version"] = 1
    room = payload["room_description"]
    for speaker in room["speakers"]:
        speaker.pop("orientation")
    for field in (
        "surface_materials",
        "covering_zones",
        "furniture",
        "acoustic_treatments",
    ):
        room.pop(field)
    return payload


def test_v3_round_trip_preserves_all_enriched_models_and_none_values():
    codec = RoomDescriptionJsonCodec()
    source = enriched_description()

    payload = codec.dumps(source)
    result = codec.loads(payload)
    raw = json.loads(payload)

    assert result.is_success
    assert result.description == source
    assert result.source_schema_version == 5
    assert not result.requires_migration
    assert raw["schema_version"] == 5
    assert raw["room_description"]["covering_zones"][0]["width_m"] is None
    assert raw["room_description"]["furniture"][0]["x_m"] is None
    assert raw["room_description"]["acoustic_treatments"][0]["surface"] is None
    assert result.description.covering_zones[0].width_m is None
    assert result.description.furniture[0].x_m is None
    assert result.description.acoustic_treatments[0].surface is None


def test_v1_is_read_completely_and_migration_is_never_silent():
    codec = RoomDescriptionJsonCodec()

    result = codec.from_dict(v1_payload())

    assert result.is_success
    assert result.source_schema_version == 1
    assert result.requires_migration
    assert result.description.speakers[0].orientation is None
    assert result.description.surface_materials == ()
    assert result.description.covering_zones == ()
    assert result.description.furniture == ()
    assert result.description.acoustic_treatments == ()

    rewritten = json.loads(codec.dumps(result.description))
    assert rewritten["schema_version"] == 5
    assert rewritten["room_description"]["surface_materials"] == []
    assert rewritten["room_description"]["speakers"][0]["orientation"] is None


def test_v3_writer_canonicalizes_collection_order_by_stable_identity():
    codec = RoomDescriptionJsonCodec()

    canonical = codec.dumps(enriched_description(), indent=2)
    reversed_input = codec.dumps(enriched_description(reverse=True), indent=2)

    assert reversed_input == canonical
    raw = json.loads(canonical)["room_description"]
    assert [item["speaker_id"] for item in raw["speakers"]] == ["LEFT", "RIGHT"]
    assert [item["zone_id"] for item in raw["covering_zones"]] == ["RUG", "WALL_FABRIC"]
    assert [item["furniture_id"] for item in raw["furniture"]] == ["SOFA", "TABLE"]
    assert [item["treatment_id"] for item in raw["acoustic_treatments"]] == ["CLOUD", "PANEL"]


def test_v2_reader_migrates_absent_planar_fields_and_writer_materializes_them():
    payload = v1_payload()
    payload["schema_version"] = 2

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert result.is_success
    assert result.requires_migration
    rewritten = RoomDescriptionJsonCodec().to_dict(result.description)
    assert rewritten["room_description"]["covering_zones"] == []
    assert rewritten["room_description"]["speakers"][0]["orientation"] is None
    assert rewritten["room_description"]["planar_surfaces"] == []
    assert rewritten["room_description"]["planar_regions"] == []


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("speakers", 0, "orientation", "yaw_degrees"), 181.0),
        (("surface_materials", 0, "surface"), "UNKNOWN"),
        (("surface_materials", 0, "material_type"), "UNKNOWN"),
        (("covering_zones", 0, "width_m"), -1.0),
        (("furniture", 0, "furniture_type"), "UNKNOWN"),
        (("acoustic_treatments", 1, "treatment_type"), "UNKNOWN"),
    ],
)
def test_v2_invalid_feature_values_return_structured_errors(path, value):
    payload = RoomDescriptionJsonCodec().to_dict(enriched_description())
    target = payload["room_description"]
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert not result.is_success
    assert result.errors[0].code is RoomDescriptionPersistenceErrorCode.INVALID_VALUE
    assert result.errors[0].path == ("room_description", *path)


def test_v3_relational_errors_withhold_partial_data_and_keep_provenance():
    payload = RoomDescriptionJsonCodec().to_dict(enriched_description())
    payload["room_description"]["covering_zones"][1].update(
        {
            "surface": "FLOOR",
            "horizontal_offset_m": 0.0,
            "vertical_offset_m": 0.0,
            "width_m": 1.0,
            "height_m": 1.0,
        }
    )
    payload["room_description"]["covering_zones"][0].update(
        {
            "horizontal_offset_m": 0.0,
            "vertical_offset_m": 0.0,
            "width_m": 1.0,
            "height_m": 1.0,
        }
    )

    result = RoomDescriptionJsonCodec().from_dict(payload)

    assert result.description is None
    assert result.source_schema_version == 5
    assert result.errors[0].code is RoomDescriptionPersistenceErrorCode.INVALID_GEOMETRY
    assert result.errors[0].validation_code is RoomDescriptionValidationCode.COVERING_ZONE_OVERLAP
    assert result.errors[0].entity_ids == ("RUG", "WALL_FABRIC")


def test_v2_payload_contains_no_invented_acoustic_coefficients():
    payload = RoomDescriptionJsonCodec().to_dict(enriched_description())

    assert payload["room_description"]["materials"] == []
    assert payload["room_description"]["material_assignments"] == []
