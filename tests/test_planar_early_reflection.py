from acousticbrain.analysis import (
    GeometryEarlyReflectionEngine,
    PlanarPropagationEngine,
    RoomGeometryBuilder,
)
from acousticbrain.models import (
    GeometryDatumQualityDescription,
    ListeningPosition,
    PlanarRegionDescription,
    PlanarRegionRole,
    PlanarSurfaceDescription,
    PlanarSurfaceRole,
    PlanarVertexDescription as Vertex,
    RoomDescription,
    RoomDimensions,
    SpeakerPosition,
)


def scene(*, region_role=None):
    surface = PlanarSurfaceDescription(
        "left_oblique",
        PlanarSurfaceRole.LEFT_WALL,
        (Vertex(0, 0, 0), Vertex(4, 0.5, 0), Vertex(4, 0.5, 2.5), Vertex(0, 0, 2.5)),
    )
    region = ()
    if region_role is not None:
        region = (PlanarRegionDescription(
            "target_region", surface.surface_id, region_role,
            (Vertex(1, 0.125, 0.5), Vertex(3, 0.375, 0.5), Vertex(3, 0.375, 1.5), Vertex(1, 0.125, 1.5)),
        ),)
    quality_ids = ("LEFT", "MIC", surface.surface_id) + (
        ("target_region",) if region_role is not None else ()
    )
    description = RoomDescription(
        "room", RoomDimensions(5, 4, 3),
        speakers=(SpeakerPosition("LEFT", 1, 1, 1),),
        listening_positions=(ListeningPosition("MIC", 3, 2, 1),),
        planar_surfaces=(surface,), planar_regions=region,
        geometry_data_quality=tuple(
            GeometryDatumQualityDescription(item, 0.01, 90, ("survey",))
            for item in quality_ids
        ),
    )
    room = RoomGeometryBuilder().from_description(description)
    return PlanarPropagationEngine().analyze(room, description).geometry


def test_derives_first_order_path_on_oblique_surface():
    propagation = scene()
    result = GeometryEarlyReflectionEngine().analyze(propagation)
    path = result.paths[0]

    assert path.base_surface_id == "left_oblique"
    assert path.path_geometry.propagation_scene_id == propagation.scene_id
    assert path.path_geometry.speaker_surface_distance_m > 0.8
    assert path.path_geometry.surface_normal[1] != 0.0
    assert path.confidence == 90


def test_excludes_impact_inside_planar_opening():
    result = GeometryEarlyReflectionEngine().analyze(
        scene(region_role=PlanarRegionRole.OPENING)
    )
    assert result.paths == ()


def test_prefers_exact_named_planar_treatment_region():
    result = GeometryEarlyReflectionEngine().analyze(
        scene(region_role=PlanarRegionRole.TREATMENT)
    )
    assert result.paths[0].surface_id == "target_region"
    assert result.paths[0].base_surface_id == "left_oblique"
