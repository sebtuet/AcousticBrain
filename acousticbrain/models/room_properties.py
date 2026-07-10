from dataclasses import dataclass


@dataclass
class RoomProperties:
    volume: float
    floor_area: float
    total_area: float
    schroeder_frequency: float
    