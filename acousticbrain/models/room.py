from dataclasses import dataclass


@dataclass
class Room:

    name: str

    length: float

    width: float

    height: float

    temperature: float = 20.0

    @property
    def volume(self) -> float:

        return self.length * self.width * self.height

    @property
    def floor_area(self) -> float:

        return self.length * self.width