from dataclasses import dataclass
from math import isfinite

from .room_description_surface import RoomDescriptionSurface
from .surface_material_description import _validate_optional_detail
from .surface_material_type import SurfaceMaterialType


@dataclass(frozen=True)
class SurfaceCoveringZone:
    """Zone rectangulaire optionnellement placée dans le repère local d'une surface."""

    zone_id: str
    surface: RoomDescriptionSurface
    material_type: SurfaceMaterialType
    detail: str | None = None
    horizontal_offset_m: float | None = None
    vertical_offset_m: float | None = None
    width_m: float | None = None
    height_m: float | None = None

    def __post_init__(self):
        _validate_identifier(self.zone_id, "Covering-zone")
        if not isinstance(self.surface, RoomDescriptionSurface):
            raise ValueError("Covering zone requires a described surface.")
        if not isinstance(self.material_type, SurfaceMaterialType):
            raise ValueError("Covering zone requires a material type.")
        _validate_optional_detail(self.detail)
        _validate_optional_rectangle(
            self.horizontal_offset_m,
            self.vertical_offset_m,
            self.width_m,
            self.height_m,
            label="Covering-zone",
        )


def _validate_identifier(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} identifier is required.")


def _validate_optional_rectangle(
    horizontal_offset_m,
    vertical_offset_m,
    width_m,
    height_m,
    *,
    label,
):
    values = (
        horizontal_offset_m,
        vertical_offset_m,
        width_m,
        height_m,
    )
    if all(value is None for value in values):
        return
    if any(value is None for value in values):
        raise ValueError(f"{label} placement must be complete or absent.")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        for value in values
    ):
        raise ValueError(f"{label} placement must contain finite numbers.")
    if min(horizontal_offset_m, vertical_offset_m) < 0.0:
        raise ValueError(f"{label} offsets cannot be negative.")
    if min(width_m, height_m) <= 0.0:
        raise ValueError(f"{label} dimensions must be positive.")
