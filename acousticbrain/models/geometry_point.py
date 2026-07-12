from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class GeometryPoint:
    """Point identifié dans le repère géométrique intérieur, en mètres."""

    point_id: str
    x_m: float
    y_m: float
    z_m: float

    def __post_init__(self):
        if not isinstance(self.point_id, str) or not self.point_id.strip():
            raise ValueError("Geometry-point identifier is required.")
        coordinates = (self.x_m, self.y_m, self.z_m)
        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            for value in coordinates
        ):
            raise ValueError("Geometry-point coordinates must be finite numbers.")
        if min(coordinates) < 0.0:
            raise ValueError("Geometry-point coordinates cannot be negative.")
