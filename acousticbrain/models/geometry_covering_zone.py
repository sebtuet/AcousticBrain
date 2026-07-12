from dataclasses import dataclass

from .geometry_material_type import GeometryMaterialType
from .geometry_surface_rectangle import GeometrySurfaceRectangle


@dataclass(frozen=True)
class GeometryCoveringZone:
    zone_id: str
    surface_id: str
    material_type: GeometryMaterialType
    detail: str | None = None
    placement: GeometrySurfaceRectangle | None = None

    def __post_init__(self):
        if not isinstance(self.zone_id, str) or not self.zone_id.strip():
            raise ValueError("Geometry covering-zone identifier is required.")
        if not isinstance(self.surface_id, str) or not self.surface_id.strip():
            raise ValueError("Geometry covering-zone surface is required.")
        if not isinstance(self.material_type, GeometryMaterialType):
            raise ValueError("Geometry covering-zone material is invalid.")
        if self.detail is not None and (
            not isinstance(self.detail, str) or not self.detail.strip()
        ):
            raise ValueError("Geometry covering-zone detail cannot be empty.")
        if self.placement is not None and not isinstance(
            self.placement, GeometrySurfaceRectangle
        ):
            raise ValueError("Geometry covering-zone placement is invalid.")
