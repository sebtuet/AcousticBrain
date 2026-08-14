from dataclasses import dataclass
from enum import Enum

from .geometry_surface_rectangle import GeometrySurfaceRectangle


class GeometryAcousticTreatmentType(Enum):
    ABSORBER = "ABSORBER"
    DIFFUSER = "DIFFUSER"
    BASS_TRAP = "BASS_TRAP"
    CEILING_CLOUD = "CEILING_CLOUD"
    OTHER = "OTHER"


@dataclass(frozen=True)
class GeometryAcousticTreatment:
    treatment_id: str
    treatment_type: GeometryAcousticTreatmentType
    detail: str | None = None
    surface_id: str | None = None
    placement: GeometrySurfaceRectangle | None = None

    def __post_init__(self):
        if not isinstance(self.treatment_id, str) or not self.treatment_id.strip():
            raise ValueError("Geometry treatment identifier is required.")
        if not isinstance(self.treatment_type, GeometryAcousticTreatmentType):
            raise ValueError("Geometry treatment type is invalid.")
        if self.detail is not None and (
            not isinstance(self.detail, str) or not self.detail.strip()
        ):
            raise ValueError("Geometry treatment detail cannot be empty.")
        if (self.surface_id is None) != (self.placement is None):
            raise ValueError("Geometry treatment placement must be complete or absent.")
        if self.surface_id is not None and (
            not isinstance(self.surface_id, str) or not self.surface_id.strip()
        ):
            raise ValueError("Geometry treatment surface identifier is invalid.")
        if self.placement is not None and not isinstance(
            self.placement, GeometrySurfaceRectangle
        ):
            raise ValueError("Geometry treatment placement is invalid.")
