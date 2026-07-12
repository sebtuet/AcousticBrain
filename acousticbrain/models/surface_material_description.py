from dataclasses import dataclass

from .room_description_surface import RoomDescriptionSurface
from .surface_material_type import SurfaceMaterialType


@dataclass(frozen=True)
class SurfaceMaterialDescription:
    """Matériau principal déclaré pour une surface complète."""

    surface: RoomDescriptionSurface
    material_type: SurfaceMaterialType
    detail: str | None = None

    def __post_init__(self):
        if not isinstance(self.surface, RoomDescriptionSurface):
            raise ValueError("Surface material requires a described surface.")
        if not isinstance(self.material_type, SurfaceMaterialType):
            raise ValueError("Surface material requires a material type.")
        _validate_optional_detail(self.detail)


def _validate_optional_detail(detail):
    if detail is not None and (
        not isinstance(detail, str) or not detail.strip()
    ):
        raise ValueError("Optional material detail cannot be empty.")
