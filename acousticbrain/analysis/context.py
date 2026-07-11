from dataclasses import dataclass, field

from acousticbrain.models import (
    ConfidenceAnalysis,
    GlobalAnalysis,
    Measurement,
    ModalDensityAnalysis,
    RecommendationAnalysis,
    RoomModesAnalysis,
    RoomProperties,
    SBIRAnalysis,
    StereoAnalysis,
    TraceabilityAnalysis,
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

    room_modes_analysis: RoomModesAnalysis | None = None

    mode_matches: list = field(default_factory=list)

    stereo: StereoAnalysis | None = None

    sbir: SBIRAnalysis | None = None

    modal_density: ModalDensityAnalysis | None = None

    confidence_analysis: ConfidenceAnalysis | None = None

    recommendation_analysis: RecommendationAnalysis | None = None

    global_analysis: GlobalAnalysis | None = None

    traceability_analysis: TraceabilityAnalysis | None = None

    room_properties: RoomProperties | None = None

    project: Project | None = None

    comparison = None
