from dataclasses import dataclass
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Mapping


class RoomGeometryComparisonStatus(Enum):
    SINGLE_SOURCE = "SINGLE_SOURCE"
    EQUIVALENT = "EQUIVALENT"
    DIVERGENT = "DIVERGENT"


@dataclass(frozen=True)
class RoomGeometryComparison:
    """Comparaison factuelle des sources, sans décision de résolution."""

    status: RoomGeometryComparisonStatus
    differing_fields: tuple[str, ...] = ()
    absolute_differences_m: Mapping[str, float] | None = None

    def __post_init__(self):
        if not isinstance(self.status, RoomGeometryComparisonStatus):
            raise ValueError("Geometry comparison requires a valid status.")
        if not isinstance(self.differing_fields, tuple):
            raise ValueError("Geometry differing fields must be a tuple.")
        if len(self.differing_fields) != len(set(self.differing_fields)):
            raise ValueError("Geometry differing fields must be unique.")
        differences = dict(self.absolute_differences_m or {})
        if tuple(differences) != self.differing_fields:
            raise ValueError("Geometry difference metrics must match their fields.")
        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not isfinite(value)
            or value < 0.0
            for value in differences.values()
        ):
            raise ValueError("Geometry differences must be finite and non-negative.")
        if bool(self.differing_fields) != (
            self.status is RoomGeometryComparisonStatus.DIVERGENT
        ):
            raise ValueError(
                "Divergent sources require explicit differing fields."
            )
        object.__setattr__(
            self,
            "absolute_differences_m",
            MappingProxyType(differences),
        )
