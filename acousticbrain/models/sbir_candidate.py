from dataclasses import dataclass

from .peak import Peak
from .reflection_surface import ReflectionSurface


@dataclass
class SBIRCandidate:
    surface: ReflectionSurface
    measured_frequency: float
    theoretical_frequency: float
    distance_m: float
    delay_ms: float
    frequency_error_hz: float
    match_score: float
    peak: Peak
