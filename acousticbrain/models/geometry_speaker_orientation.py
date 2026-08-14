from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class GeometrySpeakerOrientation:
    speaker_id: str
    yaw_degrees: float | None = None

    def __post_init__(self):
        if not isinstance(self.speaker_id, str) or not self.speaker_id.strip():
            raise ValueError("Geometry speaker identifier is required.")
        if self.yaw_degrees is None:
            return
        if (
            isinstance(self.yaw_degrees, bool)
            or not isinstance(self.yaw_degrees, (int, float))
            or not isfinite(self.yaw_degrees)
            or not -180.0 <= self.yaw_degrees <= 180.0
        ):
            raise ValueError("Geometry speaker yaw must be finite and bounded.")
