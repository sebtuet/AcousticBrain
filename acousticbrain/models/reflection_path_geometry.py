from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ReflectionPathGeometry:
    surface_normal: tuple[float, float, float]
    speaker_to_surface_direction: tuple[float, float, float]
    speaker_surface_distance_m: float
    propagation_scene_id: str

    def __post_init__(self):
        for vector in (
            self.surface_normal,
            self.speaker_to_surface_direction,
        ):
            if not isinstance(vector, tuple) or len(vector) != 3 or any(
                not isfinite(value) for value in vector
            ):
                raise ValueError("Reflection-path geometry vectors must be finite.")
        if (
            not isfinite(self.speaker_surface_distance_m)
            or self.speaker_surface_distance_m < 0.0
        ):
            raise ValueError("Speaker-surface distance must be non-negative.")
        if not isinstance(self.propagation_scene_id, str) or not self.propagation_scene_id:
            raise ValueError("Reflection path requires a propagation scene id.")
