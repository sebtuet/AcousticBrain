from enum import Enum


class SpatialBalanceStatus(Enum):
    BALANCED = "BALANCED"
    ASYMMETRIC = "ASYMMETRIC"
    UNAVAILABLE = "UNAVAILABLE"


class SpatialAlignmentStatus(Enum):
    ALIGNED = "ALIGNED"
    OFFSET = "OFFSET"
    UNAVAILABLE = "UNAVAILABLE"


class SpatialCoherenceStatus(Enum):
    COHERENT = "COHERENT"
    PARTIAL = "PARTIAL"
    WEAK = "WEAK"
    UNAVAILABLE = "UNAVAILABLE"


class SpatialStabilityStatus(Enum):
    STABLE = "STABLE"
    UNSTABLE = "UNSTABLE"
    INDETERMINATE = "INDETERMINATE"
