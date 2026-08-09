import json
from dataclasses import FrozenInstanceError, replace

import pytest

from acousticbrain.application import (
    SBIRRoomGeometryPreviewService,
    SBIRRoomGeometryResolver,
)
from acousticbrain.models import (
    SBIRRoomGeometryPreview,
    SBIRRoomGeometryResolutionDecision,
)
from test_sbir_room_geometry_resolution import declaration, experiment


def legacy_geometry():
    return {
        "coordinate_system": {
            "origin": "front_left_floor_corner",
            "unit": "m",
            "x_axis": "front_to_rear",
            "y_axis": "left_to_right",
            "z_axis": "floor_to_ceiling",
        },
        "room": {
            "dimensions": {"length": 5.0, "width": 4.0, "height": 2.5}
        },
        "loudspeakers": {
            "left": {"position": {"x": 0.8, "y": 1.0, "z": 1.1}},
            "right": {"position": {"x": 0.8, "y": 3.0, "z": 1.1}},
        },
        "listening_position": {
            "position": {"x": 3.2, "y": 2.0, "z": 1.2}
        },
    }


def resolved(tmp_path, manifest):
    directory = tmp_path / "baseline"
    directory.mkdir()
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    baseline = replace(experiment(), directory=str(directory))
    result = SBIRRoomGeometryResolver().resolve(
        declaration(), experiments=(baseline,)
    )
    return result, path


def test_preview_accepts_exact_legacy_geometry_without_writing(tmp_path):
    resolution, path = resolved(tmp_path, legacy_geometry())
    before = path.read_bytes()
    preview = SBIRRoomGeometryPreviewService().preview(resolution)
    assert isinstance(preview, SBIRRoomGeometryPreview)
    assert preview.legacy_geometry_present is True
    assert preview.decisions == tuple(SBIRRoomGeometryResolutionDecision)
    assert path.read_bytes() == before
    with pytest.raises(FrozenInstanceError):
        preview.decisions = ()


def test_preview_accepts_manifest_without_legacy_geometry(tmp_path):
    resolution, _ = resolved(tmp_path, {"state": "READY"})
    preview = SBIRRoomGeometryPreviewService().preview(resolution)
    assert preview.legacy_geometry_present is False
    assert preview.decisions[-1].value == "SBIR_GEOMETRY_DECLARATION_READY"


def test_partial_legacy_geometry_is_not_treated_as_absent(tmp_path):
    value = legacy_geometry()
    del value["room"]
    del value["listening_position"]
    resolution, _ = resolved(tmp_path, value)
    with pytest.raises(ValueError) as error:
        SBIRRoomGeometryPreviewService().preview(resolution)
    assert str(error.value) == (
        "SBIR_ROOM_GEOMETRY_LEGACY_GEOMETRY_INCOMPLETE: "
        "missing=room,listening_position."
    )


def test_conflicts_report_all_paths_in_contract_order(tmp_path):
    value = legacy_geometry()
    value["room"]["dimensions"]["length"] = 6.0
    value["loudspeakers"]["left"]["position"]["z"] = 1.2
    del value["listening_position"]["position"]["y"]
    resolution, _ = resolved(tmp_path, value)
    with pytest.raises(ValueError) as error:
        SBIRRoomGeometryPreviewService().preview(resolution)
    assert str(error.value) == (
        "SBIR_ROOM_GEOMETRY_LEGACY_GEOMETRY_CONFLICT: "
        "room.dimensions.length,loudspeakers.left.position.z,"
        "listening_position.position.y."
    )


@pytest.mark.parametrize("invalid", (True, "5.0", None, {}))
def test_non_numeric_legacy_values_are_conflicts(tmp_path, invalid):
    value = legacy_geometry()
    value["room"]["dimensions"]["length"] = invalid
    resolution, _ = resolved(tmp_path, value)
    with pytest.raises(ValueError, match="room.dimensions.length"):
        SBIRRoomGeometryPreviewService().preview(resolution)


def test_missing_or_invalid_baseline_manifest_is_explicit(tmp_path):
    directory = tmp_path / "baseline"
    directory.mkdir()
    baseline = replace(experiment(), directory=str(directory))
    resolution = SBIRRoomGeometryResolver().resolve(
        declaration(), experiments=(baseline,)
    )
    service = SBIRRoomGeometryPreviewService()
    with pytest.raises(ValueError, match="BASELINE_MANIFEST_UNAVAILABLE"):
        service.preview(resolution)
    (directory / "manifest.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="BASELINE_MANIFEST_UNAVAILABLE"):
        service.preview(resolution)


def test_preview_model_rejects_partial_decisions(tmp_path):
    resolution, _ = resolved(tmp_path, {})
    with pytest.raises(ValueError, match="decisions must be exact"):
        SBIRRoomGeometryPreview(
            resolution=resolution,
            legacy_geometry_present=False,
            decisions=(),
        )


def test_preview_service_exposes_no_write_operation():
    service = SBIRRoomGeometryPreviewService()
    assert not hasattr(service, "save")
    assert not hasattr(service, "record")
