from dataclasses import dataclass
from enum import Enum
from math import isfinite


class PlanarSurfaceRole(Enum):
    FRONT_WALL = "FRONT_WALL"
    REAR_WALL = "REAR_WALL"
    LEFT_WALL = "LEFT_WALL"
    RIGHT_WALL = "RIGHT_WALL"
    FLOOR = "FLOOR"
    CEILING = "CEILING"


class PlanarRegionRole(Enum):
    OPENING = "OPENING"
    COVERING = "COVERING"
    TREATMENT = "TREATMENT"


@dataclass(frozen=True)
class PlanarVertexDescription:
    x_m: float
    y_m: float
    z_m: float

    def __post_init__(self):
        values = (self.x_m, self.y_m, self.z_m)
        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            and value >= 0.0
            for value in values
        ):
            raise ValueError("Planar vertex coordinates must be finite and non-negative.")


@dataclass(frozen=True)
class PlanarSurfaceDescription:
    surface_id: str
    role: PlanarSurfaceRole
    vertices: tuple[PlanarVertexDescription, ...]

    def __post_init__(self):
        if not isinstance(self.surface_id, str) or not self.surface_id.strip():
            raise ValueError("Planar-surface identifier is required.")
        if not isinstance(self.role, PlanarSurfaceRole):
            raise ValueError("Planar surface requires a typed role.")
        if not isinstance(self.vertices, tuple) or any(
            not isinstance(item, PlanarVertexDescription) for item in self.vertices
        ):
            raise ValueError("Planar-surface vertices must be a typed tuple.")
        if len(self.vertices) < 3:
            raise ValueError("Planar surface requires at least three vertices.")


@dataclass(frozen=True)
class PlanarRegionDescription:
    region_id: str
    surface_id: str
    role: PlanarRegionRole
    vertices: tuple[PlanarVertexDescription, ...]
    feature_id: str | None = None

    def __post_init__(self):
        for value, label in (
            (self.region_id, "Planar-region"),
            (self.surface_id, "Planar-region surface"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} identifier is required.")
        if not isinstance(self.role, PlanarRegionRole):
            raise ValueError("Planar region requires a typed role.")
        if not isinstance(self.vertices, tuple) or any(
            not isinstance(item, PlanarVertexDescription) for item in self.vertices
        ):
            raise ValueError("Planar-region vertices must be a typed tuple.")
        if len(self.vertices) < 3:
            raise ValueError("Planar region requires at least three vertices.")
        if self.feature_id is not None and (
            not isinstance(self.feature_id, str) or not self.feature_id.strip()
        ):
            raise ValueError("Planar-region feature identifier must be non-empty.")
