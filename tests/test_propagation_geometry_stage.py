from types import SimpleNamespace

import pytest

from acousticbrain.analysis import (
    AnalysisContext,
    PropagationGeometryBuildException,
    RoomGeometryBuilder,
)
from acousticbrain.brain.stages.propagation_geometry import PropagationGeometryStage
from acousticbrain.models import (
    Measurement,
    PlanarSurfaceDescription,
    PlanarSurfaceRole,
    PlanarVertexDescription as Vertex,
    PropagationSceneSource,
    RoomDescription,
    RoomDimensions,
)


def source(planar=False):
    surfaces = (
        PlanarSurfaceDescription(
            "wall", PlanarSurfaceRole.FRONT_WALL,
            (Vertex(0, 0, 0), Vertex(0, 3, 0), Vertex(0, 3, 2.5)),
        ),
    ) if planar else ()
    return RoomDescription(
        "room", RoomDimensions(4, 3, 2.5), planar_surfaces=surfaces
    )


def context_for(description):
    context = AnalysisContext(measurement=Measurement("stereo"))
    context.room_geometry = RoomGeometryBuilder().from_description(description)
    return context


def test_stage_selects_rectangular_adapter_for_pre_v3_description():
    description = source()
    project = SimpleNamespace(
        room_description=description, propagation_geometry=None
    )
    context = context_for(description)

    PropagationGeometryStage().run(project, context)

    assert context.propagation_geometry.scene_source is PropagationSceneSource.RECTANGULAR_ADAPTER
    assert project.propagation_geometry is context.propagation_geometry


def test_stage_selects_planar_engine_when_surfaces_are_declared():
    description = source(planar=True)
    project = SimpleNamespace(
        room_description=description, propagation_geometry=None
    )
    context = context_for(description)

    PropagationGeometryStage().run(project, context)

    assert context.propagation_geometry.scene_source is PropagationSceneSource.DECLARED_PLANAR_SCENE
    assert context.propagation_geometry_analysis.geometry is context.propagation_geometry


def test_invalid_declared_scene_is_propagated_without_rectangular_fallback():
    description = source(planar=True)
    context = context_for(description)
    object.__setattr__(description.planar_surfaces[0], "vertices", (
        Vertex(0, 0, 0), Vertex(0, 1, 0), Vertex(0, 2, 0)
    ))
    project = SimpleNamespace(
        room_description=description, propagation_geometry=None
    )

    with pytest.raises(PropagationGeometryBuildException):
        PropagationGeometryStage().run(project, context)

    assert project.propagation_geometry is None
    assert context.propagation_geometry is None
