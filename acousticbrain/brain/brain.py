from acousticbrain.report import Report

from acousticbrain.analysis import AnalysisContext

from acousticbrain.analyzers import PeakDetector
from acousticbrain.classifiers import FrequencyBandClassifier

from acousticbrain.models import Room

from acousticbrain.physics import (
    ModesCalculator,
    ModeMatcher,
)

from acousticbrain.diagnostics import (
    BassDiagnostic,
    RoomModeDiagnostic,
    DipDiagnostic,
)

from acousticbrain.analyzers import DipDetector

class AcousticBrain:

    def __init__(self):

        self.diagnostics = [

            BassDiagnostic(),

            RoomModeDiagnostic(),

            DipDiagnostic(),
            

        ]

    def analyze(self, project):

        measurement = project.get_measurement("L+R")

        context = AnalysisContext(
            measurement=measurement
        )

        #
        # Calculs communs
        #

        context.peaks = PeakDetector().detect(
            measurement
        )

        context.bands = FrequencyBandClassifier().classify(
            context.peaks
        )

        room = Room(

            length=5.40,

            width=4.10,

            height=2.45,

        )

        context.room_modes = ModesCalculator().axial_modes(
            room
        )

        context.mode_matches = ModeMatcher().match(

            context.peaks,

            context.room_modes,

        )

        context.dips = DipDetector().detect(
            measurement
        )

        #
        # Rapport
        #

        report = Report(

            project_name=project.name

        )

        for diagnostic in self.diagnostics:

            report.add(

                diagnostic.analyze(
                    context
                )

            )

        return report

