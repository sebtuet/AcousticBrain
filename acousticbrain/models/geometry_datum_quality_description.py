from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class GeometryDatumQualityDescription:
    """Précision et provenance déclarées pour un objet géométrique nommé."""

    datum_id: str
    precision_m: float
    confidence: float
    provenance_codes: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.datum_id, str) or not self.datum_id.strip():
            raise ValueError("Geometry datum identifier is required.")
        if (
            isinstance(self.precision_m, bool)
            or not isinstance(self.precision_m, (int, float))
            or not isfinite(self.precision_m)
            or self.precision_m < 0.0
        ):
            raise ValueError("Geometry datum precision must be non-negative.")
        if (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, (int, float))
            or not isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 100.0
        ):
            raise ValueError("Geometry datum confidence must be bounded.")
        if (
            not isinstance(self.provenance_codes, tuple)
            or not self.provenance_codes
            or any(not isinstance(code, str) or not code for code in self.provenance_codes)
        ):
            raise ValueError("Geometry datum provenance is required.")
