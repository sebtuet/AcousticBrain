import json

import pytest

from acousticbrain.application import (
    SBIRRoomGeometryPreviewService,
    SBIRRoomGeometryRecordingService,
)
from test_sbir_room_geometry_preview import legacy_geometry, resolved


def preview(tmp_path, manifest=None):
    resolution, path = resolved(
        tmp_path, legacy_geometry() if manifest is None else manifest
    )
    return SBIRRoomGeometryPreviewService().preview(resolution), path


def test_records_only_versioned_contract_and_preserves_legacy(tmp_path):
    value, path = preview(tmp_path)
    before = json.loads(path.read_text())
    result = SBIRRoomGeometryRecordingService().record(value)
    after = json.loads(path.read_text())
    assert result.persisted is True
    assert len(result.room_description_fingerprint) == 64
    assert {key: after[key] for key in before} == before
    contract = after["room_description_contract"]
    assert contract["declaration_input_id"] == "sbir-room-geometry-001"
    assert contract["validation_decisions"][-1] == (
        "SBIR_GEOMETRY_DECLARATION_READY"
    )


def test_identical_recording_is_byte_idempotent(tmp_path):
    value, path = preview(tmp_path, {"state": "READY"})
    service = SBIRRoomGeometryRecordingService()
    assert service.record(value).persisted is True
    before = path.read_bytes()
    assert service.record(value).persisted is False
    assert path.read_bytes() == before


def test_divergent_existing_contract_is_refused_without_write(tmp_path):
    value, path = preview(tmp_path, {"state": "READY"})
    service = SBIRRoomGeometryRecordingService()
    service.record(value)
    manifest = json.loads(path.read_text())
    manifest["room_description_contract"]["declaration_source"] = "OTHER"
    path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    before = path.read_bytes()
    with pytest.raises(ValueError) as error:
        service.record(value)
    assert str(error.value) == (
        "SBIR_ROOM_GEOMETRY_DECLARATION_DIVERGENT: declaration_source."
    )
    assert path.read_bytes() == before


def test_recording_revalidates_legacy_manifest_before_write(tmp_path):
    value, path = preview(tmp_path)
    manifest = json.loads(path.read_text())
    manifest["room"]["dimensions"]["length"] = 6.0
    path.write_text(json.dumps(manifest) + "\n")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="LEGACY_GEOMETRY_CONFLICT"):
        SBIRRoomGeometryRecordingService().record(value)
    assert path.read_bytes() == before


def test_recording_requires_exact_preview():
    with pytest.raises(TypeError, match="SBIRRoomGeometryPreview"):
        SBIRRoomGeometryRecordingService().record(object())
