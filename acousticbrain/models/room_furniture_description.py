from dataclasses import dataclass
from math import isfinite

from .furniture_type import FurnitureType
from .surface_covering_zone import _validate_identifier


@dataclass(frozen=True)
class RoomFurnitureDescription:
    """Mobilier simple décrit par une boîte englobante optionnelle."""

    furniture_id: str
    furniture_type: FurnitureType
    detail: str | None = None
    x_m: float | None = None
    y_m: float | None = None
    z_m: float | None = None
    length_m: float | None = None
    width_m: float | None = None
    height_m: float | None = None

    def __post_init__(self):
        _validate_identifier(self.furniture_id, "Furniture")
        if not isinstance(self.furniture_type, FurnitureType):
            raise ValueError("Furniture requires a furniture type.")
        if self.detail is not None and (
            not isinstance(self.detail, str) or not self.detail.strip()
        ):
            raise ValueError("Optional furniture detail cannot be empty.")
        values = (
            self.x_m,
            self.y_m,
            self.z_m,
            self.length_m,
            self.width_m,
            self.height_m,
        )
        if all(value is None for value in values):
            return
        if any(value is None for value in values):
            raise ValueError("Furniture bounding box must be complete or absent.")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            for value in values
        ):
            raise ValueError("Furniture bounding box must contain finite numbers.")
        if min(self.x_m, self.y_m, self.z_m) < 0.0:
            raise ValueError("Furniture minimum-corner coordinates cannot be negative.")
        if min(self.length_m, self.width_m, self.height_m) <= 0.0:
            raise ValueError("Furniture bounding-box dimensions must be positive.")
