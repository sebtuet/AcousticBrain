from enum import Enum


class DecayUsability(Enum):
    """Exploitabilité technique d'une décroissance mesurée."""

    USABLE = "USABLE"
    INSUFFICIENT_DYNAMIC_RANGE = "INSUFFICIENT_DYNAMIC_RANGE"
    NOISE_FLOOR_REACHED = "NOISE_FLOOR_REACHED"
    UNSTABLE_SLOPE = "UNSTABLE_SLOPE"
    INSUFFICIENT_DURATION = "INSUFFICIENT_DURATION"
