from dataclasses import dataclass
from enum import Enum

from .geometry_coordinate import GeometryCoordinate


class GeometryFurnitureType(Enum):
    SOFA = "SOFA"
    CHAIR = "CHAIR"
    TABLE = "TABLE"
    SHELF = "SHELF"
    CABINET = "CABINET"
    DESK = "DESK"
    OTHER = "OTHER"


@dataclass(frozen=True)
class GeometryBox:
    minimum_corner: GeometryCoordinate
    maximum_corner: GeometryCoordinate

    def __post_init__(self):
        if not isinstance(self.minimum_corner, GeometryCoordinate) or not isinstance(
            self.maximum_corner, GeometryCoordinate
        ):
            raise ValueError("Geometry box requires global corners.")
        if any(
            minimum >= maximum
            for minimum, maximum in zip(
                (
                    self.minimum_corner.x_m,
                    self.minimum_corner.y_m,
                    self.minimum_corner.z_m,
                ),
                (
                    self.maximum_corner.x_m,
                    self.maximum_corner.y_m,
                    self.maximum_corner.z_m,
                ),
            )
        ):
            raise ValueError("Geometry box must have strictly positive dimensions.")


@dataclass(frozen=True)
class GeometryFurniture:
    furniture_id: str
    furniture_type: GeometryFurnitureType
    detail: str | None = None
    bounding_box: GeometryBox | None = None

    def __post_init__(self):
        if not isinstance(self.furniture_id, str) or not self.furniture_id.strip():
            raise ValueError("Geometry furniture identifier is required.")
        if not isinstance(self.furniture_type, GeometryFurnitureType):
            raise ValueError("Geometry furniture type is invalid.")
        if self.detail is not None and (
            not isinstance(self.detail, str) or not self.detail.strip()
        ):
            raise ValueError("Geometry furniture detail cannot be empty.")
        if self.bounding_box is not None and not isinstance(
            self.bounding_box, GeometryBox
        ):
            raise ValueError("Geometry furniture bounding box is invalid.")
