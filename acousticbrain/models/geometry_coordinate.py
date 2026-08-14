from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class GeometryCoordinate:
    """Coordonnée calculable sans identité métier."""

    x_m: float
    y_m: float
    z_m: float

    def __post_init__(self):
        values = (self.x_m, self.y_m, self.z_m)
        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            for value in values
        ):
            raise ValueError("Geometry coordinates must be finite numbers.")
        if min(values) < 0.0:
            raise ValueError("Geometry coordinates cannot be negative.")
