
from acousticbrain.diagnostics import (
    BassDiagnostic,
    RoomModeDiagnostic,
    DipDiagnostic,
    ConfidenceDiagnostic,
    ClarityDiagnostic,
    SpatialDiagnostic,
    DirectReverberantDiagnostic,
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
from .stages.spatial_analysis import SpatialAnalysisStage
from .stages.direct_reverberant_correlation import (
    DirectReverberantCorrelationStage,
)
from .stages.confidence import ConfidenceStage
from .stages.etc_correlation import ETCCorrelationStage
from .stages.clarity_correlation import ClarityCorrelationStage
from .stages.spatial_interpretation import SpatialInterpretationStage

from .stages.recommendation import RecommendationStage
from .stages.global_synthesis import GlobalSynthesisStage
from .stages.traceability import TraceabilityStage

from .builders.report import ReportBuilder

from .stages.diagnostics import DiagnosticsStage

from .stages.prioritization import PrioritizationStage

from .builders.context import ContextBuilder



class BrainPipeline:

    def __init__(self):

        self.diagnostics = [

            BassDiagnostic(),

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

            ConfidenceDiagnostic(),

        ]

    def run(self, project):

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

        GlobalSynthesisStage().run(
            context,
        )

        RecommendationStage().run(
            context,
        )

        TraceabilityStage().run(
            context,
        )

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
