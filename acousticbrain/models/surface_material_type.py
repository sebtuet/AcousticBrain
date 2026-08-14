from enum import Enum


class SurfaceMaterialType(Enum):
    """Type déclaratif sans propriété acoustique implicite."""

    WOOD = "WOOD"
    CONCRETE = "CONCRETE"
    TILE = "TILE"
    PLASTER = "PLASTER"
    BRICK = "BRICK"
    GLASS = "GLASS"
    FABRIC = "FABRIC"
    CARPET = "CARPET"
    ACOUSTIC_ASSEMBLY = "ACOUSTIC_ASSEMBLY"
    OTHER = "OTHER"
