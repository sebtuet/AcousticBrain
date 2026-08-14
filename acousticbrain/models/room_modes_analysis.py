from dataclasses import dataclass

from .room_mode import RoomMode


@dataclass
class RoomModesAnalysis:
    modes: list[RoomMode]
    axial_modes: list[RoomMode]
    tangential_modes: list[RoomMode]
    oblique_modes: list[RoomMode]
    minimum_frequency_hz: float
    maximum_frequency_hz: float
    axial_count: int
    tangential_count: int
    oblique_count: int
    total_count: int
    confidence: float

