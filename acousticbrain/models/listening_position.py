from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ListeningPosition:
    """Position d'écoute déclarée dans le repère de salle."""

    position_id: str
    x_m: float
    y_m: float
    z_m: float

    def __post_init__(self):
        if not isinstance(self.position_id, str) or not self.position_id.strip():
            raise ValueError("Listening-position identifier is required.")
        coordinates = (self.x_m, self.y_m, self.z_m)
        if not all(isfinite(value) for value in coordinates):
            raise ValueError("Listening-position coordinates must be finite.")
        if min(coordinates) < 0.0:
            raise ValueError("Listening-position coordinates cannot be negative.")
