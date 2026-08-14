from dataclasses import dataclass
from math import isfinite

from .speaker_orientation import SpeakerOrientation


@dataclass(frozen=True)
class SpeakerPosition:
    """Position déclarée d'une enceinte dans le repère de salle."""

    speaker_id: str
    x_m: float
    y_m: float
    z_m: float
    orientation: SpeakerOrientation | None = None

    def __post_init__(self):
        if not isinstance(self.speaker_id, str) or not self.speaker_id.strip():
            raise ValueError("Speaker identifier is required.")
        coordinates = (self.x_m, self.y_m, self.z_m)
        if not all(isfinite(value) for value in coordinates):
            raise ValueError("Speaker coordinates must be finite.")
        if min(coordinates) < 0.0:
            raise ValueError("Speaker coordinates cannot be negative.")
        if self.orientation is not None and not isinstance(
            self.orientation, SpeakerOrientation
        ):
            raise ValueError("Speaker orientation must be SpeakerOrientation or None.")
