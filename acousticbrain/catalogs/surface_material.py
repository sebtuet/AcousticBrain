from dataclasses import dataclass

from acousticbrain.models import (
    SurfaceMaterialCoefficient,
    SurfaceMaterialDescription,
    SurfaceMaterialPrecision,
    SurfaceMaterialQuality,
    SurfaceMaterialSource,
)


@dataclass(frozen=True)
class SurfaceMaterialCatalogEntry:
    catalog_entry_id: str
    material_type: str
    display_name: str
    material: SurfaceMaterialDescription

    def __post_init__(self):
        for value in (self.catalog_entry_id, self.material_type, self.display_name):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Material-catalog identifiers and names are required.")
        if not isinstance(self.material, SurfaceMaterialDescription):
            raise ValueError("Material-catalog entry requires a material profile.")
        if self.material.catalog_entry_id != self.catalog_entry_id:
            raise ValueError("Catalog entry and material profile identifiers must match.")


class SurfaceMaterialCatalog:
    def __init__(self, entries):
        self.entries = tuple(entries)
        if any(not isinstance(item, SurfaceMaterialCatalogEntry) for item in self.entries):
            raise ValueError("Surface-material catalog entries must be typed.")
        identifiers = tuple(item.catalog_entry_id for item in self.entries)
        types = tuple(item.material_type for item in self.entries)
        if len(identifiers) != len(set(identifiers)) or len(types) != len(set(types)):
            raise ValueError("Surface-material catalog identifiers must be unique.")
        self._by_id = {item.catalog_entry_id: item for item in self.entries}
        self._by_type = {item.material_type: item for item in self.entries}

    def get(self, catalog_entry_id):
        return self._by_id.get(catalog_entry_id)

    def get_by_type(self, material_type):
        return self._by_type.get(material_type)


def _coefficient_series(values):
    frequencies = (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0)
    return tuple(
        SurfaceMaterialCoefficient(frequency, coefficient)
        for frequency, coefficient in zip(frequencies, values)
    )


def _entry(material_type, display_name, absorption):
    catalog_entry_id = f"material.{material_type.lower()}.v1"
    material = SurfaceMaterialDescription(
        material_id=catalog_entry_id,
        display_name=display_name,
        absorption_coefficients=_coefficient_series(absorption),
        diffusion_coefficients=(),
        transmission_coefficients=None,
        source=SurfaceMaterialSource.CATALOG_ESTIMATE,
        confidence=65.0,
        quality=SurfaceMaterialQuality.ESTIMATED,
        precision=SurfaceMaterialPrecision.OCTAVE,
        provenance_codes=("INTERNAL_VERSIONED_MATERIAL_CATALOG",),
        catalog_entry_id=catalog_entry_id,
    )
    return SurfaceMaterialCatalogEntry(
        catalog_entry_id=catalog_entry_id,
        material_type=material_type,
        display_name=display_name,
        material=material,
    )


def _unknown_entry():
    catalog_entry_id = "material.unknown.v1"
    return SurfaceMaterialCatalogEntry(
        catalog_entry_id=catalog_entry_id,
        material_type="UNKNOWN",
        display_name="Unknown",
        material=SurfaceMaterialDescription(
            material_id=catalog_entry_id,
            display_name="Unknown",
            absorption_coefficients=(),
            diffusion_coefficients=(),
            source=SurfaceMaterialSource.USER_PROVIDED,
            confidence=0.0,
            quality=SurfaceMaterialQuality.UNKNOWN,
            precision=SurfaceMaterialPrecision.UNKNOWN,
            provenance_codes=("USER_DECLARED_UNKNOWN_MATERIAL",),
            catalog_entry_id=catalog_entry_id,
        ),
    )


class BuiltInSurfaceMaterialCatalog(SurfaceMaterialCatalog):
    def __init__(self):
        super().__init__((
            _entry("CONCRETE", "Concrete", (0.01, 0.01, 0.02, 0.02, 0.02, 0.03)),
            _entry("BRICK", "Brick", (0.03, 0.03, 0.03, 0.04, 0.05, 0.07)),
            _entry(
                "GYPSUM_BOARD_PAINTED",
                "Painted gypsum board",
                (0.29, 0.10, 0.05, 0.04, 0.07, 0.09),
            ),
            _entry("WOOD", "Wood", (0.15, 0.11, 0.10, 0.07, 0.06, 0.07)),
            _entry("GLAZING", "Glazing", (0.35, 0.25, 0.18, 0.12, 0.07, 0.04)),
            _unknown_entry(),
        ))
