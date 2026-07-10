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


class AcousticBrain:

    def __init__(self):

        self.diagnostics = [

            BassDiagnostic(),

            RoomModeDiagnostic(),

            DipDiagnostic(),

        ]

    def analyze(self, project):

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

        context = AnalysisContext(
            measurement=measurement
        )

        context.project = project

        #
        # Salle
        #

        room = project.room

        context.room_properties = (

            RoomAcoustics().calculate(
                room
            )

        )

        #
        # Analyse SPL (stéréo)
        #

        context.peaks = (

            PeakDetector().detect(
                measurement
            )

        )

        context.dips = (

            DipDetector().detect(
                measurement
            )

        )

        context.bands = (

            FrequencyBandClassifier().classify(
                context.peaks
            )

        )

        #
        # Analyse stéréo
        #

        left_measurement = project.get_measurement(
            Measurements.LEFT
        )

        right_measurement = project.get_measurement(
            Measurements.RIGHT
        )

        if (
            left_measurement is not None
            and right_measurement is not None
        ):

            left_peaks = PeakDetector().detect(
                left_measurement
            )

            right_peaks = PeakDetector().detect(
                right_measurement
            )

            context.stereo = (

                StereoAnalyzer().analyze(

                    left_peaks,

                    right_peaks,

                )

            )

        #
        # Modes propres
        #

        context.room_modes = (

            ModesCalculator().axial_modes(
                room
            )

        )

        context.mode_matches = (

            ModeMatcher().match(

                context.peaks,

                context.room_modes,

            )

        )

        #
        # Rapport
        #

        report = Report(

            project_name=project.name

        )

        report.room_properties = (

            context.room_properties

        )

        #
        # Diagnostics
        #

        for diagnostic in self.diagnostics:

            report.add(

                diagnostic.analyze(
                    context
                )

            )

        return report