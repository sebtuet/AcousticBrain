from dataclasses import dataclass
from math import isfinite

from .room_opening_surface import RoomOpeningSurface


@dataclass(frozen=True)
class RoomOpening:
    """Ouverture rectangulaire déclarée sur une paroi verticale."""

    opening_id: str
    surface: RoomOpeningSurface
    horizontal_offset_m: float
    vertical_offset_m: float
    width_m: float
    height_m: float

    def __post_init__(self):
        if not isinstance(self.opening_id, str) or not self.opening_id.strip():
            raise ValueError("Opening identifier is required.")
        if not isinstance(self.surface, RoomOpeningSurface):
            raise ValueError("Opening surface must be a RoomOpeningSurface.")
        values = (
            self.horizontal_offset_m,
            self.vertical_offset_m,
            self.width_m,
            self.height_m,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("Opening geometry must be finite.")
        if min(self.horizontal_offset_m, self.vertical_offset_m) < 0.0:
            raise ValueError("Opening offsets cannot be negative.")
        if min(self.width_m, self.height_m) <= 0.0:
            raise ValueError("Opening dimensions must be strictly positive.")
