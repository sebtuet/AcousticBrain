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


class RoomGeometryPresenter:
    """Projette les seuls faits géométriques déjà résolus."""

    def present(self, context):
        geometry = context.room_geometry
        comparison = context.room_geometry_comparison
        if geometry is None:
            return None
        dimensions = geometry.dimensions
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
        )
