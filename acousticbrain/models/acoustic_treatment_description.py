from dataclasses import dataclass

from .acoustic_treatment_type import AcousticTreatmentType
from .room_description_surface import RoomDescriptionSurface
from .surface_covering_zone import (
    _validate_identifier,
    _validate_optional_rectangle,
)


@dataclass(frozen=True)
class AcousticTreatmentDescription:
    """Traitement déclaré avec placement rectangulaire optionnel sur une surface."""

    treatment_id: str
    treatment_type: AcousticTreatmentType
    detail: str | None = None
    surface: RoomDescriptionSurface | None = None
    horizontal_offset_m: float | None = None
    vertical_offset_m: float | None = None
    width_m: float | None = None
    height_m: float | None = None

    def __post_init__(self):
        _validate_identifier(self.treatment_id, "Treatment")
        if not isinstance(self.treatment_type, AcousticTreatmentType):
            raise ValueError("Treatment requires an acoustic-treatment type.")
        if self.detail is not None and (
            not isinstance(self.detail, str) or not self.detail.strip()
        ):
            raise ValueError("Optional treatment detail cannot be empty.")
        placement = (
            self.surface,
            self.horizontal_offset_m,
            self.vertical_offset_m,
            self.width_m,
            self.height_m,
        )
        if all(value is None for value in placement):
            return
        if self.surface is None or not isinstance(
            self.surface, RoomDescriptionSurface
        ):
            raise ValueError("Treatment surface placement must be complete or absent.")
        if any(value is None for value in placement[1:]):
            raise ValueError("Treatment surface placement must be complete or absent.")
        _validate_optional_rectangle(
            self.horizontal_offset_m,
            self.vertical_offset_m,
            self.width_m,
            self.height_m,
            label="Treatment",
        )
