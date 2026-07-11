from acousticbrain.physics import (
    RoomAcoustics,
    ModeMatcher,
)
from acousticbrain.analysis import (
    ModalDensityAnalyzer,
    RoomModesAnalyzer,
    StereoAnalyzer,
)
from acousticbrain.project import Measurements


class PhysicsStage:
    """
    Réalise tous les calculs physiques
    liés à la salle.
    """

    ROOM_MODES_MINIMUM_FREQUENCY_HZ = 0.0
    ROOM_MODES_MAXIMUM_FREQUENCY_HZ = 300.0
    ROOM_MODES_MAXIMUM_ORDER = 4

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

        context.room_modes_analysis = RoomModesAnalyzer().analyze(
            room,
            minimum_frequency_hz=self.ROOM_MODES_MINIMUM_FREQUENCY_HZ,
            maximum_frequency_hz=self.ROOM_MODES_MAXIMUM_FREQUENCY_HZ,
            maximum_order=self.ROOM_MODES_MAXIMUM_ORDER,
        )

        context.room_modes = context.room_modes_analysis.axial_modes

        context.modal_density = ModalDensityAnalyzer().analyze(
            context.room_modes_analysis,
            context.room_properties.schroeder_frequency,
        )

        context.mode_matches = (
            ModeMatcher().match(
                context.peaks,
                context.room_modes_analysis,
            )
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
