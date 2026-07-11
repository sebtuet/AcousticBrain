from dataclasses import dataclass, field

from acousticbrain.models import (
    ConfidenceAnalysis,
    Measurement,
    ModalDensityAnalysis,
    RecommendationAnalysis,
    RoomProperties,
    SBIRAnalysis,
    StereoAnalysis,
)

from acousticbrain.project import Project


@dataclass
class AnalysisContext:

    measurement: Measurement

    peaks: list = field(default_factory=list)

    left_peaks: list = field(default_factory=list)

    right_peaks: list = field(default_factory=list)

    dips: list = field(default_factory=list)

    bands: list = field(default_factory=list)

    room_modes: list = field(default_factory=list)

    mode_matches: list = field(default_factory=list)

    stereo: StereoAnalysis | None = None

    sbir: SBIRAnalysis | None = None

    modal_density: ModalDensityAnalysis | None = None

    confidence_analysis: ConfidenceAnalysis | None = None

    recommendation_analysis: RecommendationAnalysis | None = None

    room_properties: RoomProperties | None = None

    project: Project | None = None

    comparison = None
