from dataclasses import dataclass, field

from .room_mode import RoomMode


@dataclass
class ModalBand:
    minimum_hz: float
    maximum_hz: float
    mode_count: int
    density_per_hz: float
    average_spacing_hz: float | None
    frequencies: list[float] = field(default_factory=list)
    modes: list[RoomMode] = field(default_factory=list)
