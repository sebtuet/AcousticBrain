from enum import Enum


class PeakValueConvention(Enum):
    """Étape du signal à laquelle la métadonnée peak_value s'applique."""

    SAMPLE_VALUE = "SAMPLE_VALUE"
    BEFORE_NORMALIZATION = "BEFORE_NORMALIZATION"
