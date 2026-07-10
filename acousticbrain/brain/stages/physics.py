from acousticbrain.physics import (
    RoomAcoustics,
    ModesCalculator,
    ModeMatcher,
)


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

        context.mode_matches = (
            ModeMatcher().match(
                context.peaks,
                context.room_modes,
            )
        )