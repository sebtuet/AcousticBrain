from acousticbrain.analysis import (
    GeometryEarlyReflectionEngine,
    GeometrySBIRPredictionEngine,
    PlanarPropagationEngine,
    RoomGeometryBuilder,
)
from acousticbrain.models import (
    GeometryDatumQualityDescription,
    ListeningPosition,
    PlanarSurfaceDescription,
    PlanarSurfaceRole,
    PlanarVertexDescription as Vertex,
    RoomDescription,
    RoomDimensions,
    SpeakerOrientation,
    SpeakerPosition,
)


def chain(delta=0.5):
    description = RoomDescription(
        "room", RoomDimensions(5, 4, 3),
        speakers=(SpeakerPosition("LEFT", 1, 1, 1, SpeakerOrientation(0)),),
        listening_positions=(ListeningPosition("MIC", 3, 2, 1),),
        planar_surfaces=(PlanarSurfaceDescription(
            "left_oblique", PlanarSurfaceRole.LEFT_WALL,
            (Vertex(0, 0, 0), Vertex(4, delta, 0), Vertex(4, delta, 2.5), Vertex(0, 0, 2.5)),
        ),),
        geometry_data_quality=tuple(
            GeometryDatumQualityDescription(item, 0.01, 90, ("survey",))
            for item in ("LEFT", "MIC", "left_oblique")
        ),
    )
    room = RoomGeometryBuilder().from_description(description)
    propagation = PlanarPropagationEngine().analyze(room, description).geometry
    reflections = GeometryEarlyReflectionEngine().analyze(propagation)
    return propagation, GeometrySBIRPredictionEngine().analyze(
        reflections, propagation
    )


def test_sbir_consumes_planar_path_distance_without_rectangular_recalculation():
    propagation, result = chain()
    candidate = result.candidates[0]

    assert candidate.base_surface_id == "left_oblique"
    assert candidate.speaker_boundary_distance_m == (
        GeometryEarlyReflectionEngine().analyze(propagation)
        .paths[0].path_geometry.speaker_surface_distance_m
    )
    assert candidate.relationship_code == "LEFT_SIDE_WALL"
    assert candidate.confidence == 90


def test_sbir_prediction_changes_deterministically_with_plane_geometry():
    _, first = chain(0.5)
    _, second = chain(0.8)

    assert (
        first.candidates[0].expected_cancellation_frequency_hz
        != second.candidates[0].expected_cancellation_frequency_hz
    )
