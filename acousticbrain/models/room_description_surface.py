from enum import Enum


class RoomDescriptionSurface(Enum):
    """Surface intérieure nommée dans la description utilisateur."""

    FRONT_WALL = "FRONT_WALL"
    REAR_WALL = "REAR_WALL"
    LEFT_WALL = "LEFT_WALL"
    RIGHT_WALL = "RIGHT_WALL"
    FLOOR = "FLOOR"
    CEILING = "CEILING"
