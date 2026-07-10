from dataclasses import dataclass


@dataclass
class Speaker:

    name: str

    distance_front_wall: float

    distance_side_wall: float

    height: float
    