from enum import Enum


class RoomOpeningSurface(Enum):
    """Paroi verticale portant une ouverture décrite par l'utilisateur."""

    FRONT_WALL = "FRONT_WALL"
    REAR_WALL = "REAR_WALL"
    LEFT_WALL = "LEFT_WALL"
    RIGHT_WALL = "RIGHT_WALL"
