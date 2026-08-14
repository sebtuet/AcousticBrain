from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class SpeakerOrientation:
    """Orientation déclarée autour de l'axe vertical du repère de salle."""

    yaw_degrees: float

    def __post_init__(self):
        if (
            isinstance(self.yaw_degrees, bool)
            or not isinstance(self.yaw_degrees, (int, float))
            or not isfinite(self.yaw_degrees)
        ):
            raise ValueError("Speaker yaw must be a finite number.")
        if not -180.0 <= self.yaw_degrees <= 180.0:
            raise ValueError("Speaker yaw must be between -180 and 180 degrees.")
