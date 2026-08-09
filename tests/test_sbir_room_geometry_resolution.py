from dataclasses import FrozenInstanceError, replace

import pytest

from acousticbrain.application import SBIRRoomGeometryResolver
from acousticbrain.models import (
    ExperimentDeclaration,
    ExperimentDescriptor,
    ExperimentState,
    ExperimentType,
    GeometryDatumQualityDescription,
    ListeningPosition,
    RoomDescription,
    RoomDimensions,
    SBIRRoomGeometryDeclarationInput,
    SBIRRoomGeometryResolution,
    SBIRRoomGeometryResolutionDecision,
    SpeakerPosition,
)


QUALITY_IDS = (
    "LEFT",
    "RIGHT",
    "LISTENING_POSITION",
    "front_wall",
    "rear_wall",
    "left_wall",
    "right_wall",
    "floor",
    "ceiling",
)


def room_description(**overrides):
    values = {
        "name": "Measured room",
        "dimensions": RoomDimensions(5.0, 4.0, 2.5),
        "speakers": (
            SpeakerPosition("LEFT", 0.8, 1.0, 1.1),
            SpeakerPosition("RIGHT", 0.8, 3.0, 1.1),
        ),
        "listening_positions": (
            ListeningPosition("LISTENING_POSITION", 3.2, 2.0, 1.2),
        ),
        "geometry_data_quality": tuple(
            GeometryDatumQualityDescription(
                datum_id, 0.01, 95.0, ("USER_MEASUREMENT",)
            )
            for datum_id in QUALITY_IDS
        ),
    }
    values.update(overrides)
    return RoomDescription(**values)


def declaration(description=None):
    return SBIRRoomGeometryDeclarationInput(
        schema_version=1,
        declaration_input_id="sbir-room-geometry-001",
        target_experiment_id="baseline",
        declaration_source="USER_MEASUREMENT",
        room_description=description or room_description(),
        user_note=None,
    )


def experiment(experiment_id="baseline", experiment_type=None):
    return ExperimentDescriptor(
        experiment_id=experiment_id,
        directory=f"/measurements/{experiment_id}",
        experiment_type=experiment_type or (
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
        content_hash="a" * 64,
        timestamp="2026-08-08T00:00:00+00:00",
        imported_at="2026-08-08T00:00:00+00:00",
        state=ExperimentState.INCOMPLETE,
        experiment_declaration=ExperimentDeclaration.unknown(),
    )


def resolve(value=None, experiments=None):
    return SBIRRoomGeometryResolver().resolve(
        value or declaration(),
        experiments=(experiment(),) if experiments is None else experiments,
    )


def test_resolves_exact_geometry_without_recording_or_legacy_decision():
    result = resolve()
    assert isinstance(result, SBIRRoomGeometryResolution)
    assert result.baseline_experiment.experiment_id == "baseline"
    assert {item.point_id for item in result.room_geometry.speakers} == {
        "LEFT", "RIGHT"
    }
    assert result.decisions == tuple(SBIRRoomGeometryResolutionDecision)
    assert not hasattr(result, "legacy_conflict_status")
    assert not hasattr(result, "readiness_status")
    with pytest.raises(FrozenInstanceError):
        result.decisions = ()


@pytest.mark.parametrize(
    ("experiments", "code"),
    (
        ((), "BASELINE_UNKNOWN"),
        ((experiment(), experiment()), "BASELINE_AMBIGUOUS"),
        (
            (experiment(experiment_type=ExperimentType.EXPERIMENT),),
            "BASELINE_TYPE_MISMATCH",
        ),
    ),
)
def test_baseline_resolution_is_exact(experiments, code):
    with pytest.raises(ValueError, match=code):
        resolve(experiments=experiments)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        (
            "speakers",
            (SpeakerPosition("LEFT", 0.8, 1.0, 1.1),),
            "SPEAKERS_NOT_EXACT: missing=RIGHT; extra=none",
        ),
        (
            "speakers",
            (
                SpeakerPosition("LEFT", 0.8, 1.0, 1.1),
                SpeakerPosition("RIGHT", 0.8, 3.0, 1.1),
                SpeakerPosition("CENTER", 0.8, 2.0, 1.1),
            ),
            "SPEAKERS_NOT_EXACT: missing=none; extra=CENTER",
        ),
        (
            "listening_positions",
            (),
            "LISTENING_POSITIONS_NOT_EXACT: missing=LISTENING_POSITION; extra=none",
        ),
        (
            "listening_positions",
            (
                ListeningPosition("LISTENING_POSITION", 3.2, 2.0, 1.2),
                ListeningPosition("SECOND", 3.0, 2.0, 1.2),
            ),
            "LISTENING_POSITIONS_NOT_EXACT: missing=none; extra=SECOND",
        ),
    ),
)
def test_entity_sets_are_exact(field, value, message):
    with pytest.raises(ValueError, match=message):
        resolve(declaration(room_description(**{field: value})))


def test_relational_geometry_is_validated_before_quality():
    invalid = room_description(
        speakers=(
            SpeakerPosition("LEFT", 8.0, 1.0, 1.1),
            SpeakerPosition("RIGHT", 0.8, 3.0, 1.1),
        ),
        geometry_data_quality=(),
    )
    with pytest.raises(ValueError) as error:
        resolve(declaration(invalid))
    assert str(error.value) == (
        "SBIR_ROOM_GEOMETRY_RELATIONALLY_INVALID: "
        "SPEAKER_OUTSIDE_ROOM[SPEAKER:LEFT;fields=x_m]"
    )


def test_quality_set_reports_sorted_missing_and_extra_ids():
    quality = tuple(
        item
        for item in room_description().geometry_data_quality
        if item.datum_id not in {"LEFT", "floor"}
    ) + (
        GeometryDatumQualityDescription(
            "unknown", 0.01, 95.0, ("USER_MEASUREMENT",)
        ),
    )
    with pytest.raises(ValueError) as error:
        resolve(declaration(room_description(geometry_data_quality=quality)))
    assert str(error.value) == (
        "SBIR_ROOM_GEOMETRY_QUALITY_NOT_EXACT: "
        "missing=LEFT,floor; extra=unknown."
    )


@pytest.mark.parametrize("experiments", ([], (object(),)))
def test_experiment_collection_is_explicitly_typed(experiments):
    with pytest.raises(TypeError, match="experiments"):
        SBIRRoomGeometryResolver().resolve(
            declaration(), experiments=experiments
        )


def test_resolution_is_independent_of_experiment_order():
    values = (experiment("exp-001"), experiment())
    assert resolve(experiments=values) == resolve(
        experiments=tuple(reversed(values))
    )


def test_resolution_model_rejects_inconsistent_baseline_and_decisions():
    result = resolve()
    with pytest.raises(ValueError, match="baseline is inconsistent"):
        replace(result, baseline_experiment=experiment("exp-001"))
    with pytest.raises(ValueError, match="decisions must be exact"):
        replace(result, decisions=tuple(reversed(result.decisions)))


def test_resolver_has_no_repository_or_write_operation():
    resolver = SBIRRoomGeometryResolver()
    assert not hasattr(resolver, "save")
    assert not hasattr(resolver, "repository")
