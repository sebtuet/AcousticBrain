from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedRoomGeometry:
    source: str
    model: str
    model_version: int
    length_m: float
    width_m: float
    height_m: float
    completeness: float
    comparison_status: str
    differing_fields: tuple[str, ...] = ()
    speaker_count: int = 0
    oriented_speaker_count: int = 0
    surface_material_count: int = 0
    covering_zone_count: int = 0
    placed_covering_zone_count: int = 0
    furniture_count: int = 0
    placed_furniture_count: int = 0
    treatment_count: int = 0
    placed_treatment_count: int = 0
    feature_completeness: float | None = None
    propagation_scene_id: str | None = None
    propagation_scene_version: int | None = None
    propagation_scene_source: str | None = None
    propagation_surface_count: int = 0
    propagation_region_count: int = 0
    propagation_completeness: float | None = None


class RoomGeometryPresenter:
    """Projette les seuls faits géométriques déjà résolus."""

    def present(self, context):
        geometry = context.room_geometry
        comparison = context.room_geometry_comparison
        if geometry is None:
            return None
        dimensions = geometry.dimensions
        propagation = getattr(context, "propagation_geometry", None)
        return PresentedRoomGeometry(
            source=geometry.source.value,
            model=geometry.model.value,
            model_version=geometry.model_version,
            length_m=dimensions.length_m,
            width_m=dimensions.width_m,
            height_m=dimensions.height_m,
            completeness=geometry.completeness,
            comparison_status=(
                comparison.status.value
                if comparison is not None
                else "SINGLE_SOURCE"
            ),
            differing_fields=(
                comparison.differing_fields if comparison is not None else ()
            ),
            speaker_count=len(geometry.speakers),
            oriented_speaker_count=sum(
                item.yaw_degrees is not None
                for item in geometry.speaker_orientations
            ),
            surface_material_count=len(geometry.surface_materials),
            covering_zone_count=len(geometry.covering_zones),
            placed_covering_zone_count=sum(
                item.placement is not None for item in geometry.covering_zones
            ),
            furniture_count=len(geometry.furniture),
            placed_furniture_count=sum(
                item.bounding_box is not None for item in geometry.furniture
            ),
            treatment_count=len(geometry.acoustic_treatments),
            placed_treatment_count=sum(
                item.placement is not None
                for item in geometry.acoustic_treatments
            ),
            feature_completeness=(
                geometry.feature_completeness.score
                if geometry.feature_completeness is not None
                else None
            ),
            propagation_scene_id=(
                propagation.scene_id if propagation is not None else None
            ),
            propagation_scene_version=(
                propagation.scene_version if propagation is not None else None
            ),
            propagation_scene_source=(
                propagation.scene_source.value if propagation is not None else None
            ),
            propagation_surface_count=(
                len(propagation.surfaces) if propagation is not None else 0
            ),
            propagation_region_count=(
                len(propagation.regions) if propagation is not None else 0
            ),
            propagation_completeness=(
                propagation.completeness if propagation is not None else None
            ),
        )
