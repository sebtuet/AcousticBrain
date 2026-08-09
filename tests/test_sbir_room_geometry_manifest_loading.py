import json

import pytest

from acousticbrain.application import (
    ExperimentDiscoveryService,
    SBIRRoomGeometryRecordingService,
)
from test_sbir_room_geometry_recording import preview
from test_experiment_discovery import complete_experiment


def recorded_manifest(tmp_path, manifest=None):
    value, path = preview(tmp_path, manifest)
    SBIRRoomGeometryRecordingService().record(value)
    return json.loads(path.read_text())


def test_discovery_loads_the_complete_canonical_contract(tmp_path):
    manifest = recorded_manifest(tmp_path, {"state": "READY"})
    description = ExperimentDiscoveryService._room_description(
        manifest, "baseline"
    )
    assert description.name == "Measured room"
    assert {item.speaker_id for item in description.speakers} == {
        "LEFT", "RIGHT"
    }
    assert len(description.geometry_data_quality) == 9


def test_normal_discovery_exposes_recorded_geometry_on_descriptor(tmp_path):
    recorded_manifest(tmp_path, {"state": "READY"})
    complete_experiment(tmp_path / "baseline")
    descriptor = ExperimentDiscoveryService().discover(tmp_path)[0]
    assert descriptor.experiment_id == "baseline"
    assert descriptor.room_description.name == "Measured room"
    assert len(descriptor.room_description.geometry_data_quality) == 9


def test_identical_legacy_geometry_remains_compatible(tmp_path):
    manifest = recorded_manifest(tmp_path)
    description = ExperimentDiscoveryService._room_description(
        manifest, "baseline"
    )
    assert description.dimensions.length_m == 5.0


def test_corrupted_contract_fingerprint_is_rejected(tmp_path):
    manifest = recorded_manifest(tmp_path, {"state": "READY"})
    manifest["room_description_contract"][
        "room_description_fingerprint"
    ] = "0" * 64
    with pytest.raises(ValueError, match="fingerprint is invalid"):
        ExperimentDiscoveryService._room_description(manifest, "baseline")


def test_canonical_contract_is_rejected_outside_baseline(tmp_path):
    manifest = recorded_manifest(tmp_path, {"state": "READY"})
    with pytest.raises(ValueError, match="target is inconsistent"):
        ExperimentDiscoveryService._room_description(manifest, "exp-001")


def test_post_recording_legacy_divergence_is_never_silently_preferred(tmp_path):
    manifest = recorded_manifest(tmp_path)
    manifest["loudspeakers"]["left"]["position"]["x"] = 0.9
    with pytest.raises(ValueError, match="conflicts with legacy geometry"):
        ExperimentDiscoveryService._room_description(manifest, "baseline")


def test_post_recording_partial_legacy_is_never_treated_as_absent(tmp_path):
    manifest = recorded_manifest(tmp_path)
    del manifest["room"]
    with pytest.raises(ValueError, match="incomplete legacy geometry"):
        ExperimentDiscoveryService._room_description(manifest, "baseline")


@pytest.mark.parametrize(
    "field",
    ("validation_decisions", "room_description_document", "declaration_input_id"),
)
def test_manifest_contract_is_closed_and_complete(tmp_path, field):
    manifest = recorded_manifest(tmp_path, {"state": "READY"})
    del manifest["room_description_contract"][field]
    with pytest.raises(ValueError, match="contract fields are invalid"):
        ExperimentDiscoveryService._room_description(manifest, "baseline")
