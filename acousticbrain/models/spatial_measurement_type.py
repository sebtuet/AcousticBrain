from enum import Enum


class SpatialMeasurementType(Enum):
    """Protocole d'acquisition d'une paire de signaux spatiaux."""

    SPEAKER_CHANNEL_PAIR = "SPEAKER_CHANNEL_PAIR"
    BINAURAL_PAIR = "BINAURAL_PAIR"
