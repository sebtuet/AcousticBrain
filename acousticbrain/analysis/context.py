from dataclasses import dataclass, field

from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayCorrelationAnalysis,
    ClarityAnalysis,
    ClarityCorrelationAnalysis,
    ConfidenceAnalysis,
    ETCAnalysis,
    DirectReverberantAnalysis,
    DirectReverberantCorrelationAnalysis,
    ETCReflectionCorrelationAnalysis,
    GlobalAnalysis,
    Measurement,
    MeasurementQualityAnalysis,
    MeasurementReadinessAnalysis,
    ModalDensityAnalysis,
    RecommendationAnalysis,
    RT60Analysis,
    RoomModesAnalysis,
    RoomProperties,
    RoomGeometry,
    RoomGeometryComparison,
    SBIRAnalysis,
    BinauralSpatialInterpretation,
    SpatialAnalysis,
    SpatialCorrelationAnalysis,
    SpeakerPairSpatialInterpretation,
    StereoAnalysis,
    TraceabilityAnalysis,
    AcousticReasoningAnalysis,
    ExperimentPlanningAnalysis,
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

    measurement_quality_analysis: MeasurementQualityAnalysis | None = None

    measurement_readiness_analysis: MeasurementReadinessAnalysis | None = None

    rt60_analysis: RT60Analysis | None = None

    etc_analysis: ETCAnalysis | None = None

    clarity_analysis: ClarityAnalysis | None = None

    direct_reverberant_analysis: DirectReverberantAnalysis | None = None

    bass_decay_analysis: BassDecayAnalysis | None = None

    bass_decay_correlation_analysis: BassDecayCorrelationAnalysis | None = None

    direct_reverberant_correlation_analysis: (
        DirectReverberantCorrelationAnalysis | None
    ) = None

    clarity_correlation_analysis: ClarityCorrelationAnalysis | None = None

    spatial_analysis: SpatialAnalysis | None = None

    spatial_interpretation: (
        SpeakerPairSpatialInterpretation
        | BinauralSpatialInterpretation
        | None
    ) = None

    spatial_correlation_analysis: SpatialCorrelationAnalysis | None = None

    etc_reflection_correlation_analysis: (
        ETCReflectionCorrelationAnalysis | None
    ) = None

    confidence_analysis: ConfidenceAnalysis | None = None

    recommendation_analysis: RecommendationAnalysis | None = None

    acoustic_reasoning_analysis: AcousticReasoningAnalysis | None = None

    experiment_planning_analysis: ExperimentPlanningAnalysis | None = None

    global_analysis: GlobalAnalysis | None = None

    traceability_analysis: TraceabilityAnalysis | None = None

    room_properties: RoomProperties | None = None

    room_geometry: RoomGeometry | None = None

    room_geometry_comparison: RoomGeometryComparison | None = None

    project: Project | None = None

    comparison = None

    optimization_session = None

    optimization_session_analysis = None

    experiment_descriptors: tuple = ()
