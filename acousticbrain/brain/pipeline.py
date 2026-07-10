
from acousticbrain.diagnostics import (
    BassDiagnostic,
    RoomModeDiagnostic,
    DipDiagnostic,
    StereoDiagnostic,
)

from acousticbrain.project import Measurements

from .stages.analysis import AnalysisStage

from .stages.physics import PhysicsStage

from .builders.report import ReportBuilder

from .stages.diagnostics import DiagnosticsStage

from .builders.context import ContextBuilder



class BrainPipeline:

    def __init__(self):

        self.diagnostics = [

            BassDiagnostic(),

            RoomModeDiagnostic(),

            DipDiagnostic(),

            StereoDiagnostic(),

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
