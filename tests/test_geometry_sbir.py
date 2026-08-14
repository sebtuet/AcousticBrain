from dataclasses import replace

import pytest

from acousticbrain.analysis import (
    GeometryEarlyReflectionEngine,
    GeometrySBIRPredictionEngine,
    RoomGeometryBuilder,
    SBIRGeometryCorrelationEngine,
)
from acousticbrain.models import (
    GeometryDatumQualityDescription,
    ListeningPosition,
    Peak,
    ReflectionSurface,
    RoomDescription,
    RoomDescriptionSurface,
    RoomDimensions,
    SpeakerOrientation,
    SpeakerPosition,
    SurfaceCoveringZone,
    SurfaceMaterialType,
)


def geometry(*, quality=True):
    datum_ids = (
        "LEFT",
        "MIC",
        "front_wall",
        "rear_wall",
        "left_wall",
        "right_wall",
        "floor",
        "ceiling",
    )
    description = RoomDescription(
        "SBIR reference",
        RoomDimensions(5.0, 4.0, 3.0),
        speakers=(
            SpeakerPosition(
                "LEFT", 1.0, 1.0, 1.0, SpeakerOrientation(0.0)
            ),
        ),
        listening_positions=(ListeningPosition("MIC", 3.0, 1.0, 1.0),),
        geometry_data_quality=(
            tuple(
                GeometryDatumQualityDescription(
                    item,
                    precision_m=0.01,
                    confidence=88.0,
                    provenance_codes=("LASER_MEASURED",),
                )
                for item in datum_ids
            )
            if quality else ()
        ),
    )
    return RoomGeometryBuilder().from_description(description)


def prediction(*, quality=True):
    room = geometry(quality=quality)
    reflections = GeometryEarlyReflectionEngine().analyze(room)
    return GeometrySBIRPredictionEngine().analyze(reflections, room)


def test_predicts_six_first_order_rectangular_sbir_candidates():
    result = prediction()

    assert len(result.candidates) == 6
    assert {item.surface for item in result.candidates} == set(ReflectionSurface)
    front = next(
        item for item in result.candidates
        if item.surface is ReflectionSurface.FRONT_WALL
    )
    assert front.relationship_code == "WALL_BEHIND_SPEAKER"
    assert front.direct_path_m == pytest.approx(2.0)
    assert front.reflected_path_m == pytest.approx(4.0)
    assert front.extra_distance_m == pytest.approx(2.0)
    assert front.speaker_boundary_distance_m == pytest.approx(1.0)
    assert front.expected_cancellation_frequency_hz == pytest.approx(85.75)
    assert front.distance_uncertainty_m == pytest.approx(0.06)
    assert front.frequency_uncertainty_hz == pytest.approx(2.5725)
    assert front.confidence == 88.0
    assert front.provenance_codes == ("LASER_MEASURED",)


def test_preserves_unknown_geometry_quality_without_inventing_it():
    front = next(
        item for item in prediction(quality=False).candidates
        if item.surface is ReflectionSurface.FRONT_WALL
    )

    assert front.distance_uncertainty_m is None
    assert front.frequency_uncertainty_hz is None
    assert front.confidence is None
    assert front.provenance_codes == ()


def test_preserves_named_rectangular_region_as_physical_candidate():
    description = RoomDescription(
        "Named SBIR region",
        RoomDimensions(5.0, 4.0, 3.0),
        speakers=(SpeakerPosition("LEFT", 1.0, 1.0, 1.0),),
        listening_positions=(ListeningPosition("MIC", 3.0, 1.0, 1.0),),
        covering_zones=(SurfaceCoveringZone(
            "FRONT_PANEL_02",
            RoomDescriptionSurface.FRONT_WALL,
            SurfaceMaterialType.FABRIC,
            horizontal_offset_m=0.5,
            vertical_offset_m=0.5,
            width_m=1.0,
            height_m=1.0,
        ),),
    )
    room = RoomGeometryBuilder().from_description(description)
    paths = GeometryEarlyReflectionEngine().analyze(room)

    result = GeometrySBIRPredictionEngine().analyze(paths, room)

    front = next(
        item for item in result.candidates
        if item.base_surface_id == "front_wall"
    )
    assert front.surface_id == "FRONT_PANEL_02"
    assert front.base_surface_id == "front_wall"


def test_correlates_prediction_with_observed_dip_without_causal_result():
    geometry_analysis = prediction()
    front = next(
        item for item in geometry_analysis.candidates
        if item.surface is ReflectionSurface.FRONT_WALL
    )
    unrelated = replace(
        front,
        candidate_id="geometry_sbir.unrelated",
        expected_cancellation_frequency_hz=200.0,
        frequency_uncertainty_hz=6.0,
    )
    geometry_analysis = replace(
        geometry_analysis,
        candidates=(front, unrelated),
    )

    result = SBIRGeometryCorrelationEngine().analyze(
        geometry_analysis,
        (
            Peak(86.0, 50.0, 1, 12.0),
            Peak(300.0, 55.0, 2, 8.0),
        ),
    )

    assert len(result.correlations) == 1
    match = result.best_match
    assert match.candidate is front
    assert match.observed_dip.frequency == 86.0
    assert match.frequency_error_hz == pytest.approx(0.25)
    assert match.frequency_error_percent == pytest.approx(0.291545, rel=1e-5)
    assert "CAUSAL" not in match.code
    assert "SBIR_COMPATIBILITY_IS_NOT_CAUSAL_PROOF" in (
        result.applied_rule_codes
    )
    assert result.unmatched_candidate_ids == ("geometry_sbir.unrelated",)


def test_correlation_is_deterministic_when_dips_are_equidistant():
    front = next(
        item for item in prediction().candidates
        if item.surface is ReflectionSurface.FRONT_WALL
    )
    source = replace(prediction(), candidates=(front,))

    result = SBIRGeometryCorrelationEngine().analyze(
        source,
        (Peak(85.5, 50.0, 2, 10.0), Peak(86.0, 50.0, 1, 10.0)),
    )

    assert result.best_match.observed_dip.frequency == 85.5
