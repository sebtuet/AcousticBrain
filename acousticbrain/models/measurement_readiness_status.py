from enum import Enum


class MeasurementReadinessStatus(Enum):
    AVAILABLE = "AVAILABLE"
    AVAILABLE_WITH_RESERVATIONS = "AVAILABLE_WITH_RESERVATIONS"
    BLOCKED = "BLOCKED"


class MeasurementAnalysisFamily(Enum):
    FREQUENCY = "FREQUENCY"
    RT60 = "RT60"
    ETC = "ETC"
    CLARITY = "CLARITY"
    SPATIAL = "SPATIAL"
    DIRECT_REVERBERANT = "DIRECT_REVERBERANT"
    BASS_DECAY = "BASS_DECAY"
