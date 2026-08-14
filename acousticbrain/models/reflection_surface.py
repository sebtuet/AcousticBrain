from enum import Enum, auto


class ReflectionSurface(Enum):
    FRONT_WALL = auto()
    REAR_WALL = auto()
    LEFT_WALL = auto()
    RIGHT_WALL = auto()
    FLOOR = auto()
    CEILING = auto()
