
from acousticbrain.diagnostics import (
    BassDiagnostic,
    RoomModeDiagnostic,
    DipDiagnostic,
    ConfidenceDiagnostic,
    ClarityDiagnostic,
    SpatialDiagnostic,
    DirectReverberantDiagnostic,
    BassDecayDiagnostic,
    MeasurementQualityDiagnostic,
    AcousticReasoningDiagnostic,
    ETCDiagnostic,
    ModalDensityDiagnostic,
    RT60Diagnostic,
    SBIRDiagnostic,
    StereoDiagnostic,
)

from acousticbrain.project import Measurements

from .stages.analysis import AnalysisStage

from .stages.physics import PhysicsStage
from .stages.temporal_analysis import TemporalAnalysisStage
from .stages.measurement_quality import MeasurementQualityStage
from .stages.measurement_readiness import MeasurementReadinessStage
from .stages.room_geometry import RoomGeometryStage
from .stages.propagation_geometry import PropagationGeometryStage
from .stages.surface_material import SurfaceMaterialStage
from .stages.spatial_analysis import SpatialAnalysisStage
from .stages.direct_reverberant_correlation import (
    DirectReverberantCorrelationStage,
)
from .stages.bass_decay_correlation import BassDecayCorrelationStage
from .stages.confidence import ConfidenceStage
from .stages.etc_correlation import ETCCorrelationStage
from .stages.material_aware_reflection_candidate import (
    MaterialAwareReflectionCandidateStage,
)
from .stages.reflection_verification_planning import (
    ControlledReflectionVerificationPlanningStage,
)
from .stages.reflection_experiment_declaration import (
    ControlledReflectionExperimentDeclarationStage,
)
from .stages.reflection_experiment_comparison import (
    ControlledReflectionExperimentComparisonStage,
)
from .stages.reflection_hypothesis_status_update import (
    ControlledReflectionHypothesisStatusUpdateStage,
)
from .stages.geometry_early_reflection import GeometryEarlyReflectionStage
from .stages.geometry_sbir import GeometrySBIRStage
from .stages.sbir_geometry_correlation import SBIRGeometryCorrelationStage
from .stages.clarity_correlation import ClarityCorrelationStage
from .stages.spatial_interpretation import SpatialInterpretationStage

from .stages.recommendation import RecommendationStage
from .stages.global_synthesis import GlobalSynthesisStage
from .stages.traceability import TraceabilityStage
from .stages.acoustic_reasoning import AcousticReasoningStage
from .stages.experiment_planning import ExperimentPlanningStage
from .stages.loudspeaker_positioning_experiment import (
    LoudspeakerPositioningExperimentStage,
)
from .stages.acoustic_hypothesis_experiment_generation import (
    AcousticHypothesisExperimentGenerationStage,
)
from .stages.listening_position_campaign_plan import (
    ListeningPositionCampaignPlanStage,
)
from .stages.campaign_reference_qualification import (
    CampaignReferenceQualificationStage,
)
from .stages.acoustic_observation import AcousticObservationStage
from .stages.deterministic_acoustic_reasoning import (
    DeterministicAcousticReasoningStage,
)
from .stages.deterministic_corrective_action import (
    DeterministicCorrectiveActionStage,
)

from .builders.report import ReportBuilder

from .stages.diagnostics import DiagnosticsStage

from .stages.prioritization import PrioritizationStage

from .builders.context import ContextBuilder



class BrainPipeline:

    def __init__(self):

        self.diagnostics = [

            MeasurementQualityDiagnostic(),

            BassDiagnostic(),

            BassDecayDiagnostic(),

            RoomModeDiagnostic(),

            DipDiagnostic(),

            StereoDiagnostic(),

            SBIRDiagnostic(),

            ModalDensityDiagnostic(),

            RT60Diagnostic(),

            ETCDiagnostic(),

            ClarityDiagnostic(),

            SpatialDiagnostic(),

            DirectReverberantDiagnostic(),

            AcousticReasoningDiagnostic(),

            ConfidenceDiagnostic(),

        ]

    def run(
        self,
        project,
        *,
        session_context=None,
        plan_experiments=False,
        experiment_descriptors=(),
        listening_position_sampling_protocol=None,
        listening_position_campaign_instance_analysis=None,
        campaign_reference_qualification_declaration_analysis=None,
        longitudinal_experimental_learning_analysis=None,
        synthesize_observations=False,
        synthesize_reasoning=False,
        synthesize_actions=False,
        return_context=False,
    ):

        synthesize_reasoning = synthesize_reasoning or synthesize_actions
        synthesize_observations = synthesize_observations or synthesize_reasoning

        #
        # Mesure principale
        #

        measurement = project.get_measurement(
            Measurements.STEREO
        )

        if measurement is None:

            raise ValueError(
                "Aucune mesure stéréo n'a été trouvée."
            )

        #
        # Contexte
        #

        context = ContextBuilder().build(
        project,
        measurement,
        )
        context.experiment_descriptors = tuple(experiment_descriptors)
        context.listening_position_sampling_protocol = (
            listening_position_sampling_protocol
        )
        context.listening_position_campaign_instance_analysis = (
            listening_position_campaign_instance_analysis
        )
        context.campaign_reference_qualification_declaration_analysis = (
            campaign_reference_qualification_declaration_analysis
        )
        context.longitudinal_experimental_learning_analysis = (
            longitudinal_experimental_learning_analysis
        )

        RoomGeometryStage().run(
            project,
            context,
        )

        PropagationGeometryStage().run(
            project,
            context,
        )

        SurfaceMaterialStage().run(
            project,
            context,
        )

        MeasurementQualityStage().run(
            project,
            context,
        )

        MeasurementReadinessStage().run(
            context,
        )
        
        AnalysisStage().run(
            project,
            context,
        )

        PhysicsStage().run(
            project,
            context,
        )

        TemporalAnalysisStage().run(
            project,
            context,
        )

        SpatialAnalysisStage().run(
            project,
            context,
        )

        DirectReverberantCorrelationStage().run(
            context,
        )

        BassDecayCorrelationStage().run(
            context,
        )

        ConfidenceStage().run(
            context,
        )

        GeometryEarlyReflectionStage().run(
            context,
        )

        GeometrySBIRStage().run(
            context,
        )

        SBIRGeometryCorrelationStage().run(
            context,
        )

        ETCCorrelationStage().run(
            context,
        )

        MaterialAwareReflectionCandidateStage().run(
            context,
        )

        ControlledReflectionVerificationPlanningStage().run(
            context,
        )

        ControlledReflectionExperimentDeclarationStage().run(
            project,
            context,
        )

        ControlledReflectionExperimentComparisonStage().run(
            project,
            context,
        )

        ControlledReflectionHypothesisStatusUpdateStage().run(
            project,
            context,
        )

        ClarityCorrelationStage().run(
            context,
        )

        SpatialInterpretationStage().run(
            context,
        )

        if synthesize_observations:
            AcousticObservationStage().run(context)

        AcousticReasoningStage().run(
            context,
        )

        if synthesize_reasoning:
            DeterministicAcousticReasoningStage().run(context)

        if synthesize_actions:
            DeterministicCorrectiveActionStage().run(context)

        AcousticHypothesisExperimentGenerationStage().run(
            context,
        )

        CampaignReferenceQualificationStage().run(
            context,
        )

        ListeningPositionCampaignPlanStage().run(
            context,
        )

        if plan_experiments:
            ExperimentPlanningStage().run(
                context,
                session=(
                    session_context.session
                    if session_context is not None
                    else None
                ),
            )

        GlobalSynthesisStage().run(
            context,
        )

        RecommendationStage().run(
            context,
        )

        LoudspeakerPositioningExperimentStage().run(
            context,
        )

        TraceabilityStage().run(
            context,
        )

        if session_context is not None:
            session_context.record_analysis(context)
            context.optimization_session = session_context.session

        report = ReportBuilder().build(
            project,
            context,
        )

        DiagnosticsStage(
            self.diagnostics
        ).run(
            context,
            report,
        )

        PrioritizationStage().run(report)

        return (report, context) if return_context else report
