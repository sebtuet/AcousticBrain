from dataclasses import dataclass, field

from .modal_band import ModalBand


@dataclass
class ModalDensityAnalysis:
    bands: list[ModalBand] = field(default_factory=list)
    total_mode_count: int = 0
    axial_mode_count: int = 0
    tangential_mode_count: int = 0
    oblique_mode_count: int = 0
    average_spacing_hz: float | None = None
    minimum_spacing_hz: float | None = None
    maximum_spacing_hz: float | None = None
    sparse_bands: list[ModalBand] = field(default_factory=list)
    dense_bands: list[ModalBand] = field(default_factory=list)
    score: float = 0.0
    confidence: float = 0.0
