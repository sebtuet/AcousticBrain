from dataclasses import dataclass


@dataclass
class Room:

    length: float

    width: float

    height: float

    temperature: float = 20.0
    