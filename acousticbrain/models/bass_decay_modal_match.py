from dataclasses import dataclass

from .room_mode_type import RoomModeType


@dataclass(frozen=True)
class BassDecayModalMatch:
    """Correspondance traçable entre une bande Bass Decay et un mode."""

    band_center_frequency_hz: float
    mode_frequency_hz: float
    mode_type: RoomModeType
    order_x: int
    order_y: int
    order_z: int
    frequency_error_hz: float

    def __post_init__(self):
        if self.band_center_frequency_hz <= 0.0:
            raise ValueError("Band center frequency must be positive.")
        if self.mode_frequency_hz <= 0.0:
            raise ValueError("Mode frequency must be positive.")
        if min(self.order_x, self.order_y, self.order_z) < 0:
            raise ValueError("Mode indices cannot be negative.")
        expected = abs(
            self.mode_frequency_hz - self.band_center_frequency_hz
        )
        if abs(self.frequency_error_hz - expected) > 1e-9:
            raise ValueError(
                "Frequency error must match the mode-to-band distance."
            )
