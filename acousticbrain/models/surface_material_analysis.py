from dataclasses import dataclass
from math import isfinite

from .surface_material_assignment import SurfaceMaterialAssignment
from .surface_material_description import SurfaceMaterialDescription


@dataclass(frozen=True)
class SurfaceMaterialTargetAvailability:
    target_kind: str
    target_id: str
    material_id: str | None
    provenance_codes: tuple[str, ...] = ()

    def __post_init__(self):
        if self.target_kind not in {"SURFACE", "REGION"}:
            raise ValueError("Material availability requires a supported target kind.")
        if not isinstance(self.target_id, str) or not self.target_id.strip():
            raise ValueError("Material availability requires a target identifier.")
        if self.material_id is not None and (
            not isinstance(self.material_id, str) or not self.material_id.strip()
        ):
            raise ValueError("Material availability has an invalid material identifier.")
        if not isinstance(self.provenance_codes, tuple):
            raise ValueError("Material-availability provenance must be a tuple.")


@dataclass(frozen=True)
class SurfaceMaterialAnalysis:
    materials: tuple[SurfaceMaterialDescription, ...]
    assignments: tuple[SurfaceMaterialAssignment, ...]
    target_availability: tuple[SurfaceMaterialTargetAvailability, ...]
    available_material_ids: tuple[str, ...]
    missing_material_target_codes: tuple[str, ...]
    completeness: float
    available_fact_codes: tuple[str, ...]
    missing_fact_codes: tuple[str, ...]
    source_analysis_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]

    def __post_init__(self):
        typed = (
            (self.materials, SurfaceMaterialDescription),
            (self.assignments, SurfaceMaterialAssignment),
            (self.target_availability, SurfaceMaterialTargetAvailability),
        )
        for collection, expected in typed:
            if not isinstance(collection, tuple) or any(
                not isinstance(item, expected) for item in collection
            ):
                raise ValueError("Surface-material analysis contains invalid data.")
        for collection in (
            self.available_material_ids,
            self.missing_material_target_codes,
            self.available_fact_codes,
            self.missing_fact_codes,
            self.source_analysis_codes,
            self.applied_rule_codes,
        ):
            if not isinstance(collection, tuple):
                raise ValueError("Surface-material analysis facts must be tuples.")
        if not isfinite(self.completeness) or not 0.0 <= self.completeness <= 100.0:
            raise ValueError("Surface-material completeness must be bounded.")
