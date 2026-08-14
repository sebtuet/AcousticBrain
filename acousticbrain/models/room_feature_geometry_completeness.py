from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class RoomFeatureGeometryCompleteness:
    orientation_coverage: float
    material_coverage: float
    covering_placement_coverage: float
    furniture_placement_coverage: float
    treatment_placement_coverage: float
    score: float

    def __post_init__(self):
        values = (
            self.orientation_coverage,
            self.material_coverage,
            self.covering_placement_coverage,
            self.furniture_placement_coverage,
            self.treatment_placement_coverage,
            self.score,
        )
        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            and 0.0 <= value <= 100.0
            for value in values
        ):
            raise ValueError("Feature completeness values must be between 0 and 100.")
