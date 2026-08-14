from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class GeometryDatumQuality:
    datum_id: str
    precision_m: float
    confidence: float
    provenance_codes: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.datum_id, str) or not self.datum_id.strip():
            raise ValueError("Geometry quality identifier is required.")
        if not isfinite(self.precision_m) or self.precision_m < 0.0:
            raise ValueError("Geometry quality precision must be non-negative.")
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Geometry quality confidence must be bounded.")
        if not isinstance(self.provenance_codes, tuple) or not self.provenance_codes:
            raise ValueError("Geometry quality provenance is required.")
