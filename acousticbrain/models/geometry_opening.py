from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class GeometryOpening:
    """Ouverture rectangulaire rattachable à une surface géométrique."""

    opening_id: str
    surface_id: str
    horizontal_offset_m: float
    vertical_offset_m: float
    width_m: float
    height_m: float

    def __post_init__(self):
        for value, label in (
            (self.opening_id, "Opening"),
            (self.surface_id, "Opening surface"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} identifier is required.")
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
            raise ValueError("Geometry-opening values must be finite numbers.")
        if min(self.horizontal_offset_m, self.vertical_offset_m) < 0.0:
            raise ValueError("Geometry-opening offsets cannot be negative.")
        if min(self.width_m, self.height_m) <= 0.0:
            raise ValueError("Geometry-opening dimensions must be positive.")
