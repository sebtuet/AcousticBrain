from acousticbrain.analysis import (
    AnalysisContext,
    StereoAnalyzer,
)

from acousticbrain.analyzers import (
    PeakDetector,
    DipDetector,
)

from acousticbrain.classifiers import (
    FrequencyBandClassifier,
)

from acousticbrain.diagnostics import (
    BassDiagnostic,
    RoomModeDiagnostic,
    DipDiagnostic,
)

from acousticbrain.physics import (
    RoomAcoustics,
    ModesCalculator,
    ModeMatcher,
)

from acousticbrain.project import Measurements

from acousticbrain.report import Report

from .stages.analysis import AnalysisStage

from .stages.physics import PhysicsStage

from .builders.report import ReportBuilder

from .stages.diagnostics import DiagnosticsStage




class BrainPipeline:

    def __init__(self):

        self.diagnostics = [

            BassDiagnostic(),

            RoomModeDiagnostic(),

            DipDiagnostic(),

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

        from .builders.context import ContextBuilder

        ...

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

        context.mode_matches = (

            ModeMatcher().match(

                context.peaks,

                context.room_modes,

            )

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

        return report