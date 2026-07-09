from dataclasses import dataclass

from acousticbrain.models import Peak, RoomMode


@dataclass
class ModeMatch:

    peak: Peak

    mode: RoomMode

    error_hz: float

    confidence: float
    