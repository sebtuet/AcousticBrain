from dataclasses import dataclass
from math import isfinite

from .surface_material_description import SurfaceMaterialDescriptionSource


@dataclass(frozen=True)
class SurfaceMaterialAssignment:
    assignment_id: str
    material_id: str
    surface_id: str | None = None
    region_id: str | None = None
    description_source: SurfaceMaterialDescriptionSource = (
        SurfaceMaterialDescriptionSource.IMPORTED_PROJECT_DATA
    )
    description_confidence: float = 0.0
    provenance_codes: tuple[str, ...] = ()

    def __post_init__(self):
        for value, label in (
            (self.assignment_id, "assignment"),
            (self.material_id, "material"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Surface-material {label} identifier is required.")
        targets = (self.surface_id, self.region_id)
        if sum(value is not None for value in targets) != 1:
            raise ValueError("Material assignment requires exactly one target.")
        if any(
            value is not None and (not isinstance(value, str) or not value.strip())
            for value in targets
        ):
            raise ValueError("Material-assignment target identifier is invalid.")
        if not isinstance(self.description_source, SurfaceMaterialDescriptionSource):
            raise ValueError("Material assignment requires a description source.")
        if (
            isinstance(self.description_confidence, bool)
            or not isinstance(self.description_confidence, (int, float))
            or not isfinite(self.description_confidence)
            or not 0.0 <= self.description_confidence <= 100.0
        ):
            raise ValueError("Material-assignment confidence must be bounded.")
        if not isinstance(self.provenance_codes, tuple) or any(
            not isinstance(item, str) or not item.strip()
            for item in self.provenance_codes
        ):
            raise ValueError("Material-assignment provenance must contain codes.")

    @property
    def target_kind(self):
        return "SURFACE" if self.surface_id is not None else "REGION"

    @property
    def target_id(self):
        return self.surface_id if self.surface_id is not None else self.region_id
