from dataclasses import dataclass


@dataclass(frozen=True)
class SurfaceMaterialAssignment:
    assignment_id: str
    material_id: str
    surface_id: str | None = None
    region_id: str | None = None

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

    @property
    def target_kind(self):
        return "SURFACE" if self.surface_id is not None else "REGION"

    @property
    def target_id(self):
        return self.surface_id if self.surface_id is not None else self.region_id
