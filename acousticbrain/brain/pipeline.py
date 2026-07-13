
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
from .stages.spatial_analysis import SpatialAnalysisStage
from .stages.direct_reverberant_correlation import (
    DirectReverberantCorrelationStage,
)
from .stages.bass_decay_correlation import BassDecayCorrelationStage
from .stages.confidence import ConfidenceStage
from .stages.etc_correlation import ETCCorrelationStage
from .stages.clarity_correlation import ClarityCorrelationStage
from .stages.spatial_interpretation import SpatialInterpretationStage

from .stages.recommendation import RecommendationStage
from .stages.global_synthesis import GlobalSynthesisStage
from .stages.traceability import TraceabilityStage
from .stages.acoustic_reasoning import AcousticReasoningStage
from .stages.experiment_planning import ExperimentPlanningStage

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
    ):

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

        RoomGeometryStage().run(
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

        ETCCorrelationStage().run(
            context,
        )

        ClarityCorrelationStage().run(
            context,
        )

        SpatialInterpretationStage().run(
            context,
        )

        AcousticReasoningStage().run(
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

        return report
