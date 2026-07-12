from dataclasses import dataclass

from .geometry_material_type import GeometryMaterialType


@dataclass(frozen=True)
class GeometrySurfaceMaterial:
    surface_id: str
    material_type: GeometryMaterialType
    detail: str | None = None

    def __post_init__(self):
        if not isinstance(self.surface_id, str) or not self.surface_id.strip():
            raise ValueError("Geometry material surface identifier is required.")
        if not isinstance(self.material_type, GeometryMaterialType):
            raise ValueError("Geometry material type is invalid.")
        if self.detail is not None and (
            not isinstance(self.detail, str) or not self.detail.strip()
        ):
            raise ValueError("Geometry material detail cannot be empty.")
