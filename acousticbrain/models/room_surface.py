from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .geometry_point import GeometryPoint


class RoomSurfaceKind(Enum):
    FRONT_WALL = "FRONT_WALL"
    REAR_WALL = "REAR_WALL"
    LEFT_WALL = "LEFT_WALL"
    RIGHT_WALL = "RIGHT_WALL"
    FLOOR = "FLOOR"
    CEILING = "CEILING"


@dataclass(frozen=True)
class RoomSurface:
    """Surface rectangulaire nommée, sans propriété acoustique."""

    surface_id: str
    kind: RoomSurfaceKind
    origin: GeometryPoint
    width_m: float
    height_m: float

    def __post_init__(self):
        if not isinstance(self.surface_id, str) or not self.surface_id.strip():
            raise ValueError("Room-surface identifier is required.")
        if not isinstance(self.kind, RoomSurfaceKind):
            raise ValueError("Room surface requires a RoomSurfaceKind.")
        if not isinstance(self.origin, GeometryPoint):
            raise ValueError("Room surface requires a GeometryPoint origin.")
        dimensions = (self.width_m, self.height_m)
        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            for value in dimensions
        ) or min(dimensions) <= 0.0:
            raise ValueError("Room-surface dimensions must be positive and finite.")
