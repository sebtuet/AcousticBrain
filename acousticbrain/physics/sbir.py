from acousticbrain.models import (
    Speaker,
    SBIRMode,
)


class SBIRCalculator:

    SPEED_OF_SOUND = 343.0

    def calculate(self, speaker: Speaker):

        modes = []

        #
        # Mur avant
        #

        front = self.SPEED_OF_SOUND / (
            4 * speaker.distance_front_wall
        )

        modes.append(

            SBIRMode(

                surface="Front Wall",

                frequency=front,

                distance=speaker.distance_front_wall,

            )

        )

        #
        # Mur latéral
        #

        side = self.SPEED_OF_SOUND / (
            4 * speaker.distance_side_wall
        )

        modes.append(

            SBIRMode(

                surface="Side Wall",

                frequency=side,

                distance=speaker.distance_side_wall,

            )

        )

        return modes