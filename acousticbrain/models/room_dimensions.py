from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class RoomDimensions:
    """Dimensions intérieures déclarées d'une salle, en mètres."""

    length_m: float
    width_m: float
    height_m: float

    def __post_init__(self):
        values = (self.length_m, self.width_m, self.height_m)
        if not all(isfinite(value) for value in values):
            raise ValueError("Room dimensions must be finite.")
        if min(values) <= 0.0:
            raise ValueError("Room dimensions must be strictly positive.")
