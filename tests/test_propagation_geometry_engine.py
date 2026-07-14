import pytest

from acousticbrain.analysis import (
    PlanarPropagationEngine,
    PropagationGeometryBuildException,
    PropagationGeometryEngine,
    RectangularPropagationEngine,
    RoomGeometryBuilder,
)
from acousticbrain.models import (
    GeometryDatumQualityDescription,
    ListeningPosition,
    PlanarSurfaceDescription,
    PlanarSurfaceRole,
    PlanarVertexDescription as Vertex,
    PropagationSceneSource,
    RoomDescription,
    RoomDimensions,
    SpeakerPosition,
)


def description(*, planar=True, reverse=False, delta=0.0):
    surfaces = ()
    if planar:
        vertices = (
            Vertex(0, 0, 0), Vertex(4, 0.5 + delta, 0),
            Vertex(4, 0.5 + delta, 2.5), Vertex(0, 0, 2.5),
        )
        surfaces = (PlanarSurfaceDescription(
            "left_real", PlanarSurfaceRole.LEFT_WALL,
            tuple(reversed(vertices)) if reverse else vertices,
        ),)
    return RoomDescription(
        "room", RoomDimensions(5, 4, 3),
        speakers=(SpeakerPosition("LEFT", 1, 1, 1),),
        listening_positions=(ListeningPosition("MIC", 3, 2, 1),),
        planar_surfaces=surfaces,
        geometry_data_quality=(
            GeometryDatumQualityDescription("LEFT", 0.01, 90, ("survey",)),
        ),
    )


def geometry(source):
    return RoomGeometryBuilder().from_description(source)


def test_propagation_engine_is_an_explicit_abstraction():
    with pytest.raises(TypeError):
        PropagationGeometryEngine()


def test_rectangular_adapter_builds_six_surfaces_and_stable_identity():
    source = description(planar=False)
    first = RectangularPropagationEngine().analyze(geometry(source), source)
    second = RectangularPropagationEngine().analyze(geometry(source), source)

    assert first.geometry.scene_source is PropagationSceneSource.RECTANGULAR_ADAPTER
    assert len(first.geometry.surfaces) == 6
    assert first.geometry.completeness == 100.0
    assert first.geometry.scene_id == second.geometry.scene_id


def test_planar_engine_derives_oblique_plane_and_preserves_quality():
    source = description()
    result = PlanarPropagationEngine().analyze(geometry(source), source)
    surface = result.geometry.surfaces[0]

    assert result.geometry.scene_source is PropagationSceneSource.DECLARED_PLANAR_SCENE
    assert surface.surface_id == "left_real"
    assert surface.area_m2 > 10.0
    assert surface.normal[1] != 0.0
    assert result.geometry.data_quality[0].provenance_codes == ("survey",)
    assert result.missing_fact_codes


def test_scene_id_is_winding_independent_but_changes_with_geometry():
    normal = description()
    reversed_source = description(reverse=True)
    changed = description(delta=0.1)

    identifiers = [
        PlanarPropagationEngine().analyze(geometry(item), item).geometry.scene_id
        for item in (normal, reversed_source, changed)
    ]

    assert identifiers[0] == identifiers[1]
    assert identifiers[0] != identifiers[2]


def test_declared_invalid_scene_never_falls_back_to_rectangular_adapter():
    source = description()
    rectangular_geometry = geometry(source)
    invalid = source.planar_surfaces[0]
    object.__setattr__(invalid, "vertices", (
        Vertex(0, 0, 0), Vertex(1, 0, 0), Vertex(2, 0, 0)
    ))

    with pytest.raises(PropagationGeometryBuildException):
        PlanarPropagationEngine().analyze(rectangular_geometry, source)
