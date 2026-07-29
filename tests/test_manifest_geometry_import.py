import json
import shutil

import pytest

from acousticbrain.application import AcousticSession, ExperimentDiscoveryService
from acousticbrain.brain import AcousticBrain
from acousticbrain.importers import ExperimentImporter
from acousticbrain.analysis import RoomGeometryBuilder
from acousticbrain.models import (
    ExperimentDeclaration,
    ExperimentDescriptor,
    ExperimentKind,
    ExperimentState,
    ExperimentType,
)
from historical_campaign import HISTORICAL_CAMPAIGN_ROOT


FULL_GEOMETRY_CONTROLS = (
    "LISTENING_POSITION",
    "LOUDSPEAKER_POSITION",
    "MICROPHONE_POSITION",
    "ROOM_CONFIGURATION",
)


def geometry(*, left_x=0.54):
    return {
        "coordinate_system": {
            "front_wall": "wall_behind_loudspeakers",
            "origin": "front_left_floor_corner",
            "rear_wall": "wall_behind_listening_position",
            "unit": "m",
            "x_axis": "front_to_rear",
            "y_axis": "left_to_right",
            "z_axis": "floor_to_ceiling",
        },
        "room": {
            "dimensions": {"height": 2.6, "length": 5.84, "width": 5.5}
        },
        "loudspeakers": {
            "left": {"position": {"x": left_x, "y": 0.79, "z": 0.87}},
            "right": {"position": {"x": 0.51, "y": 3.22, "z": 0.87}},
        },
        "listening_position": {
            "position": {"x": 3.0, "y": 1.91, "z": 0.92}
        },
    }


def descriptor(
    experiment_id,
    *,
    room_description=None,
    reference=None,
    controls=(),
):
    declaration = (
        ExperimentDeclaration(
            schema_version=1,
            experiment_kind=ExperimentKind.MEASUREMENT_REPEAT,
            reference_experiment_code=reference,
            modified_variables=("MEASUREMENT_ACQUISITION",),
            controlled_variables=tuple(controls),
            user_note=None,
            field_provenance=(
                ("controlled_variables", "TEST"),
                ("experiment_kind", "TEST"),
                ("modified_variables", "TEST"),
                ("reference_experiment_code", "TEST"),
                ("user_note", "TEST"),
            ),
        )
        if reference is not None
        else ExperimentDeclaration.unknown()
    )
    return ExperimentDescriptor(
        experiment_id=experiment_id,
        directory=f"/measurements/{experiment_id}",
        experiment_type=(
            ExperimentType.BASELINE
            if experiment_id == "baseline"
            else ExperimentType.EXPERIMENT
        ),
        available_files=(),
        available_channels=(),
        wav_files=(),
        txt_files=(),
        mdat_file=None,
        manifest_present=True,
        content_hash=f"hash-{experiment_id}",
        timestamp="2026-07-29T00:00:00",
        imported_at="2026-07-29T00:00:00+00:00",
        state=ExperimentState.READY,
        experiment_declaration=declaration,
        room_description=room_description,
    )


def parsed_geometry(*, left_x=0.54, experiment_id="baseline"):
    return ExperimentDiscoveryService._room_description(
        geometry(left_x=left_x),
        experiment_id,
    )


def test_complete_local_manifest_geometry_reaches_project_room_description():
    local = parsed_geometry(experiment_id="exp-001")

    project = ExperimentImporter().load(
        descriptor("exp-001", room_description=local)
    )

    assert project.room_description is local
    assert tuple(item.speaker_id for item in project.room_description.speakers) == (
        "LEFT",
        "RIGHT",
    )
    assert project.room.width == 5.5


def test_missing_local_geometry_inherits_from_explicit_controlled_reference():
    reference = parsed_geometry()
    descriptors = (
        descriptor("baseline", room_description=reference),
        descriptor(
            "exp-001",
            reference="baseline",
            controls=FULL_GEOMETRY_CONTROLS,
        ),
    )

    resolved = AcousticSession._resolve_geometry(descriptors)

    assert resolved["exp-001"] is reference


@pytest.mark.parametrize(
    ("reference", "controls"),
    (
        (None, FULL_GEOMETRY_CONTROLS),
        ("baseline", ("ROOM_CONFIGURATION",)),
        ("missing", FULL_GEOMETRY_CONTROLS),
    ),
)
def test_missing_local_geometry_is_not_invented(reference, controls):
    descriptors = (
        descriptor("baseline", room_description=parsed_geometry()),
        descriptor("exp-001", reference=reference, controls=controls),
    )

    resolved = AcousticSession._resolve_geometry(descriptors)

    assert "exp-001" not in resolved


def test_reference_without_geometry_does_not_create_geometry():
    descriptors = (
        descriptor("baseline"),
        descriptor(
            "exp-001",
            reference="baseline",
            controls=FULL_GEOMETRY_CONTROLS,
        ),
    )

    assert "exp-001" not in AcousticSession._resolve_geometry(descriptors)


def test_reference_with_incomplete_geometry_does_not_create_geometry():
    incomplete = geometry()
    del incomplete["loudspeakers"]["right"]["position"]["z"]

    reference_geometry = ExperimentDiscoveryService._room_description(
        incomplete,
        "baseline",
    )
    descriptors = (
        descriptor("baseline", room_description=reference_geometry),
        descriptor(
            "exp-001",
            reference="baseline",
            controls=FULL_GEOMETRY_CONTROLS,
        ),
    )

    assert reference_geometry is None
    assert "exp-001" not in AcousticSession._resolve_geometry(descriptors)


def test_local_geometry_has_priority_when_reference_is_not_controlled():
    reference = parsed_geometry()
    local = parsed_geometry(left_x=0.6, experiment_id="exp-001")
    descriptors = (
        descriptor("baseline", room_description=reference),
        descriptor(
            "exp-001",
            room_description=local,
            reference="baseline",
            controls=("ROOM_CONFIGURATION",),
        ),
    )

    assert AcousticSession._resolve_geometry(descriptors)["exp-001"] is local


def test_conflicting_local_and_controlled_reference_geometry_is_rejected():
    descriptors = (
        descriptor("baseline", room_description=parsed_geometry()),
        descriptor(
            "exp-001",
            room_description=parsed_geometry(
                left_x=0.6,
                experiment_id="exp-001",
            ),
            reference="baseline",
            controls=FULL_GEOMETRY_CONTROLS,
        ),
    )

    with pytest.raises(ValueError, match="Controlled manifest geometry conflicts"):
        AcousticSession._resolve_geometry(descriptors)


def test_historical_manifest_without_geometry_keeps_legacy_import_behavior():
    assert ExperimentDiscoveryService._room_description({}, "exp-001") is None

    project = ExperimentImporter().load(descriptor("exp-001"))

    assert project.room_description is None
    assert (project.room.length, project.room.width, project.room.height) == (
        5.84,
        5.51,
        2.60,
    )


def test_inherited_manifest_geometry_reaches_evidence_acquisition_path(tmp_path):
    measurement_root = tmp_path / "measurements"
    for experiment_id in ("baseline", "exp-001"):
        shutil.copytree(
            HISTORICAL_CAMPAIGN_ROOT / experiment_id,
            measurement_root / experiment_id,
        )

    baseline_manifest_path = measurement_root / "baseline" / "manifest.json"
    baseline_manifest = json.loads(baseline_manifest_path.read_text())
    baseline_manifest.update(geometry())
    baseline_manifest_path.write_text(
        json.dumps(baseline_manifest, indent=2, sort_keys=True) + "\n"
    )

    experiment_manifest_path = measurement_root / "exp-001" / "manifest.json"
    experiment_manifest = json.loads(experiment_manifest_path.read_text())
    experiment_manifest["experiment_declaration"] = {
        "schema_version": 1,
        "experiment_kind": "MEASUREMENT_REPEAT",
        "reference_experiment_code": "baseline",
        "modified_variables": ["MEASUREMENT_ACQUISITION"],
        "controlled_variables": list(FULL_GEOMETRY_CONTROLS),
        "user_note": None,
        "field_provenance": {
            "experiment_kind": "TEST",
            "reference_experiment_code": "TEST",
            "modified_variables": "TEST",
            "controlled_variables": "TEST",
            "user_note": "TEST",
        },
    }
    experiment_manifest_path.write_text(
        json.dumps(experiment_manifest, indent=2, sort_keys=True) + "\n"
    )

    report = AcousticBrain().analyze(
        measurement_root=measurement_root,
        compare_experiments=True,
        synthesize_evidence_acquisition=True,
    )

    project = AcousticSession.auto_open(measurement_root).current_project
    assert project.room_description is not None
    assert len(
        RoomGeometryBuilder().from_description(project.room_description).speakers
    ) == 2
    asymmetry = next(
        item
        for item in report.deterministic_acoustic_reasoning.reasonings
        if item.reasoning_id == "ASYMMETRIC_SPEAKER_ROOM_INTERACTION_REASONING"
    )
    assert "room_geometry.stereo_speaker_positions" not in asymmetry.limitations
