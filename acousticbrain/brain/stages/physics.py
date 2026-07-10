from acousticbrain.physics import (
    RoomAcoustics,
    ModesCalculator,
    ModeMatcher,
)
from acousticbrain.analysis import (
    ModalDensityAnalyzer,
    PeakClassifier,
    StereoAnalyzer,
)
from acousticbrain.project import Measurements


class PhysicsStage:
    """
    Réalise tous les calculs physiques
    liés à la salle.
    """

    def run(self, project, context):

        room = project.room

        #
        # Caractéristiques de la salle
        #

        context.room_properties = (
            RoomAcoustics().calculate(
                room
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

        context.modal_density = ModalDensityAnalyzer().analyze(
            context.room_modes,
            context.room_properties.schroeder_frequency,
        )

        context.mode_matches = (
            ModeMatcher().match(
                context.peaks,
                context.room_modes,
            )
        )

        context.peak_classification = PeakClassifier().analyze(
            context.peaks,
            context.mode_matches,
            context.room_modes,
            context.sbir,
        )

        left_measurement = project.get_measurement(Measurements.LEFT)
        right_measurement = project.get_measurement(Measurements.RIGHT)

        if left_measurement is not None and right_measurement is not None:
            context.stereo = StereoAnalyzer().analyze(
                context.left_peaks,
                context.right_peaks,
                room_modes=context.room_modes,
                left_measurement=left_measurement,
                right_measurement=right_measurement,
            )
