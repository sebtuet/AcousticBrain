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
    GeometryEarlyReflectionAnalysis,
    GeometrySBIRAnalysis,
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
    SBIRGeometryCorrelationAnalysis,
    BinauralSpatialInterpretation,
    SpatialAnalysis,
    SpatialCorrelationAnalysis,
    SpeakerPairSpatialInterpretation,
    StereoAnalysis,
    TraceabilityAnalysis,
    AcousticReasoningAnalysis,
    ExperimentPlanningAnalysis,
    LoudspeakerPositioningExperimentAnalysis,
    ListeningPositionSamplingProtocol,
    ListeningPositionCampaignPlan,
    ListeningPositionCampaignInstanceAnalysis,
    CampaignReferenceQualification,
    CampaignReferenceQualificationDeclarationAnalysis,
    AcousticObservationSynthesis,
    DeterministicAcousticReasoningSynthesis,
    DeterministicCorrectiveActionSynthesis,
    DeterministicEvidenceWeightingSynthesis,
    EvidenceAcquisitionPlanSynthesis,
    PropagationGeometry,
    PropagationGeometryAnalysis,
    SurfaceMaterialAnalysis,
    MaterialAwareReflectionCandidateAnalysis,
    ControlledReflectionVerificationPlanningAnalysis,
    ControlledReflectionExperimentDeclaration,
    ControlledReflectionExperimentComparison,
    ControlledReflectionHypothesisStatusUpdate,
)

from acousticbrain.project import Project


@dataclass
class AnalysisContext:

    measurement: Measurement

    acoustic_observation_synthesis: AcousticObservationSynthesis | None = None

    deterministic_acoustic_reasoning_synthesis: (
        DeterministicAcousticReasoningSynthesis | None
    ) = None

    deterministic_corrective_action_synthesis: (
        DeterministicCorrectiveActionSynthesis | None
    ) = None

    deterministic_evidence_weighting_synthesis: (
        DeterministicEvidenceWeightingSynthesis | None
    ) = None

    evidence_acquisition_plan_synthesis: EvidenceAcquisitionPlanSynthesis | None = None

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

    geometry_early_reflection_analysis: GeometryEarlyReflectionAnalysis | None = None

    geometry_sbir_analysis: GeometrySBIRAnalysis | None = None

    sbir_geometry_correlation_analysis: (
        SBIRGeometryCorrelationAnalysis | None
    ) = None

    confidence_analysis: ConfidenceAnalysis | None = None

    recommendation_analysis: RecommendationAnalysis | None = None

    acoustic_reasoning_analysis: AcousticReasoningAnalysis | None = None

    experiment_planning_analysis: ExperimentPlanningAnalysis | None = None

    acoustic_hypothesis_experiment_generation_analysis = None

    loudspeaker_positioning_experiment_analysis: (
        LoudspeakerPositioningExperimentAnalysis | None
    ) = None

    experiment_campaign_analyses: tuple = ()

    longitudinal_experimental_learning_analysis = None

    global_analysis: GlobalAnalysis | None = None

    traceability_analysis: TraceabilityAnalysis | None = None

    room_properties: RoomProperties | None = None

    room_geometry: RoomGeometry | None = None

    room_geometry_comparison: RoomGeometryComparison | None = None

    propagation_geometry: PropagationGeometry | None = None

    propagation_geometry_analysis: PropagationGeometryAnalysis | None = None

    surface_material_analysis: SurfaceMaterialAnalysis | None = None

    material_aware_reflection_candidate_analysis: (
        MaterialAwareReflectionCandidateAnalysis | None
    ) = None

    controlled_reflection_verification_planning_analysis: (
        ControlledReflectionVerificationPlanningAnalysis | None
    ) = None

    controlled_reflection_experiment_declarations: tuple[
        ControlledReflectionExperimentDeclaration, ...
    ] = ()

    controlled_reflection_experiment_comparisons: tuple[
        ControlledReflectionExperimentComparison, ...
    ] = ()

    controlled_reflection_hypothesis_status_updates: tuple[
        ControlledReflectionHypothesisStatusUpdate, ...
    ] = ()

    project: Project | None = None

    comparison = None

    optimization_session = None

    optimization_session_analysis = None

    experiment_descriptors: tuple = ()

    listening_position_sampling_protocol: (
        ListeningPositionSamplingProtocol | None
    ) = None

    listening_position_campaign_plan: ListeningPositionCampaignPlan | None = None

    listening_position_campaign_instance_analysis: (
        ListeningPositionCampaignInstanceAnalysis | None
    ) = None

    campaign_reference_qualification_declaration_analysis: (
        CampaignReferenceQualificationDeclarationAnalysis | None
    ) = None

    campaign_reference_qualification: CampaignReferenceQualification | None = None

    experiment_comparison_analysis = None

    causal_discrimination_analysis = None
