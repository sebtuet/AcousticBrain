from enum import Enum


class GeometrySource(Enum):
    """Provenance exclusive d'une géométrie calculable."""

    LEGACY_ROOM = "LEGACY_ROOM"
    ROOM_DESCRIPTION = "ROOM_DESCRIPTION"
