from acousticbrain.analyzers import (
    PeakDetector,
    DipDetector,
)

from acousticbrain.classifiers import (
    FrequencyBandClassifier,
)

from acousticbrain.project import Measurements


class AnalysisStage:
    """
    Réalise toutes les analyses liées
    aux mesures acoustiques.
    """

    def run(self, project, context):

        measurement = context.measurement

        #
        # Analyse SPL principale
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
            left_measurement is None
            or right_measurement is None
        ):
            return

        left_peaks = (
            PeakDetector().detect(
                left_measurement
            )
        )

        right_peaks = (
            PeakDetector().detect(
                right_measurement
            )
        )

        context.left_peaks = left_peaks
        context.right_peaks = right_peaks
