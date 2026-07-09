from dataclasses import dataclass


@dataclass
class RoomMode:
    axis: str
    order: int
    frequency: float
    