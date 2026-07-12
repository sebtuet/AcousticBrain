from dataclasses import dataclass
from math import isfinite

from .geometry_coordinate import GeometryCoordinate


@dataclass(frozen=True)
class GeometrySurfaceRectangle:
    """Rectangle local accompagné de ses deux coins globaux extrêmes."""

    horizontal_offset_m: float
    vertical_offset_m: float
    width_m: float
    height_m: float
    minimum_corner: GeometryCoordinate
    maximum_corner: GeometryCoordinate

    def __post_init__(self):
        values = (
            self.horizontal_offset_m,
            self.vertical_offset_m,
            self.width_m,
            self.height_m,
        )
        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            for value in values
        ):
            raise ValueError("Geometry rectangle values must be finite.")
        if min(values[:2]) < 0.0 or min(values[2:]) <= 0.0:
            raise ValueError("Geometry rectangle offsets and dimensions are invalid.")
        if not isinstance(self.minimum_corner, GeometryCoordinate) or not isinstance(
            self.maximum_corner, GeometryCoordinate
        ):
            raise ValueError("Geometry rectangle requires global corners.")
