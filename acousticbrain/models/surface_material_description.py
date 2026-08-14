from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .room_description_surface import RoomDescriptionSurface
from .surface_material_type import SurfaceMaterialType


class SurfaceMaterialSource(Enum):
    DECLARED = "DECLARED"
    MANUFACTURER = "MANUFACTURER"
    MEASURED = "MEASURED"
    DATABASE = "DATABASE"
    MANUFACTURER_DATA = "MANUFACTURER_DATA"
    CATALOG_ESTIMATE = "CATALOG_ESTIMATE"
    USER_PROVIDED = "USER_PROVIDED"


class SurfaceMaterialDescriptionSource(Enum):
    USER_DESCRIPTION_INTERPRETED = "USER_DESCRIPTION_INTERPRETED"
    USER_STRUCTURED_INPUT = "USER_STRUCTURED_INPUT"
    IMPORTED_PROJECT_DATA = "IMPORTED_PROJECT_DATA"


class SurfaceMaterialQuality(Enum):
    UNKNOWN = "UNKNOWN"
    ESTIMATED = "ESTIMATED"
    DECLARED = "DECLARED"
    VERIFIED = "VERIFIED"


class SurfaceMaterialPrecision(Enum):
    UNKNOWN = "UNKNOWN"
    BROADBAND = "BROADBAND"
    OCTAVE = "OCTAVE"
    THIRD_OCTAVE = "THIRD_OCTAVE"


@dataclass(frozen=True)
class SurfaceMaterialCoefficient:
    center_frequency_hz: float
    coefficient: float

    def __post_init__(self):
        if (
            isinstance(self.center_frequency_hz, bool)
            or not isinstance(self.center_frequency_hz, (int, float))
            or not isfinite(self.center_frequency_hz)
            or self.center_frequency_hz <= 0.0
        ):
            raise ValueError("Material-band frequency must be positive and finite.")
        if (
            isinstance(self.coefficient, bool)
            or not isinstance(self.coefficient, (int, float))
            or not isfinite(self.coefficient)
            or not 0.0 <= self.coefficient <= 1.0
        ):
            raise ValueError("Material coefficient must be between zero and one.")


@dataclass(frozen=True, init=False)
class SurfaceMaterialDescription:
    """Profil fréquentiel descriptif, avec compatibilité du contrat v2 legacy."""

    material_id: str
    display_name: str
    absorption_coefficients: tuple[SurfaceMaterialCoefficient, ...]
    diffusion_coefficients: tuple[SurfaceMaterialCoefficient, ...]
    transmission_coefficients: tuple[SurfaceMaterialCoefficient, ...] | None
    source: SurfaceMaterialSource
    confidence: float
    quality: SurfaceMaterialQuality
    precision: SurfaceMaterialPrecision
    provenance_codes: tuple[str, ...]
    catalog_entry_id: str | None
    legacy_surface: RoomDescriptionSurface | None
    legacy_material_type: SurfaceMaterialType | None
    legacy_detail: str | None

    def __init__(
        self,
        material_id=None,
        display_name=None,
        absorption_coefficients=(),
        diffusion_coefficients=(),
        transmission_coefficients=None,
        source=SurfaceMaterialSource.DECLARED,
        confidence=0.0,
        quality=SurfaceMaterialQuality.UNKNOWN,
        precision=SurfaceMaterialPrecision.UNKNOWN,
        provenance_codes=(),
        catalog_entry_id=None,
        *,
        surface=None,
        material_type=None,
        detail=None,
    ):
        positional_legacy = isinstance(material_id, RoomDescriptionSurface)
        if positional_legacy:
            surface = material_id
            material_type = display_name
            if absorption_coefficients not in ((), None):
                detail = absorption_coefficients
        legacy = surface is not None or material_type is not None
        if legacy:
            if not isinstance(surface, RoomDescriptionSurface):
                raise ValueError("Surface material requires a described surface.")
            if not isinstance(material_type, SurfaceMaterialType):
                raise ValueError("Surface material requires a material type.")
            _validate_optional_detail(detail)
            values = {
                "material_id": f"legacy:{surface.value.lower()}",
                "display_name": material_type.value,
                "absorption_coefficients": (),
                "diffusion_coefficients": (),
                "transmission_coefficients": None,
                "source": SurfaceMaterialSource.DECLARED,
                "confidence": 0.0,
                "quality": SurfaceMaterialQuality.UNKNOWN,
                "precision": SurfaceMaterialPrecision.UNKNOWN,
                "provenance_codes": ("LEGACY_SURFACE_MATERIAL_DECLARATION",),
                "catalog_entry_id": None,
                "legacy_surface": surface,
                "legacy_material_type": material_type,
                "legacy_detail": detail,
            }
        else:
            values = {
                "material_id": material_id,
                "display_name": display_name,
                "absorption_coefficients": absorption_coefficients,
                "diffusion_coefficients": diffusion_coefficients,
                "transmission_coefficients": transmission_coefficients,
                "source": source,
                "confidence": confidence,
                "quality": quality,
                "precision": precision,
                "provenance_codes": provenance_codes,
                "catalog_entry_id": catalog_entry_id,
                "legacy_surface": None,
                "legacy_material_type": None,
                "legacy_detail": None,
            }
        for name, value in values.items():
            object.__setattr__(self, name, value)
        self._validate()

    @property
    def is_legacy(self):
        return self.legacy_surface is not None

    @property
    def surface(self):
        return self.legacy_surface

    @property
    def material_type(self):
        return self.legacy_material_type

    @property
    def detail(self):
        return self.legacy_detail

    def _validate(self):
        if not isinstance(self.material_id, str) or not self.material_id.strip():
            raise ValueError("Surface-material identifier is required.")
        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise ValueError("Surface-material display name is required.")
        for name, coefficients in (
            ("absorption", self.absorption_coefficients),
            ("diffusion", self.diffusion_coefficients),
        ):
            self._validate_coefficients(name, coefficients)
        if self.transmission_coefficients is not None:
            self._validate_coefficients("transmission", self.transmission_coefficients)
        if not isinstance(self.source, SurfaceMaterialSource):
            raise ValueError("Surface material requires a typed source.")
        if (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, (int, float))
            or not isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 100.0
        ):
            raise ValueError("Surface-material confidence must be bounded.")
        if not isinstance(self.quality, SurfaceMaterialQuality):
            raise ValueError("Surface material requires typed quality.")
        if not isinstance(self.precision, SurfaceMaterialPrecision):
            raise ValueError("Surface material requires typed precision.")
        if not isinstance(self.provenance_codes, tuple) or any(
            not isinstance(item, str) or not item.strip()
            for item in self.provenance_codes
        ):
            raise ValueError("Surface-material provenance must be a tuple of codes.")
        if len(self.provenance_codes) != len(set(self.provenance_codes)):
            raise ValueError("Surface-material provenance codes must be unique.")
        if self.catalog_entry_id is not None and (
            not isinstance(self.catalog_entry_id, str)
            or not self.catalog_entry_id.strip()
        ):
            raise ValueError("Surface-material catalog identifier cannot be empty.")
        if (
            self.source is SurfaceMaterialSource.CATALOG_ESTIMATE
            and self.catalog_entry_id is None
        ):
            raise ValueError("Catalog estimates require an immutable catalog entry.")

    @staticmethod
    def _validate_coefficients(name, coefficients):
        if not isinstance(coefficients, tuple) or any(
            not isinstance(item, SurfaceMaterialCoefficient) for item in coefficients
        ):
            raise ValueError(f"Surface-material {name} coefficients must be typed.")
        frequencies = tuple(item.center_frequency_hz for item in coefficients)
        if frequencies != tuple(sorted(frequencies)):
            raise ValueError(f"Surface-material {name} bands must be sorted.")
        if len(frequencies) != len(set(frequencies)):
            raise ValueError(f"Surface-material {name} bands must be unique.")


def _validate_optional_detail(detail):
    if detail is not None and (not isinstance(detail, str) or not detail.strip()):
        raise ValueError("Optional material detail cannot be empty.")
