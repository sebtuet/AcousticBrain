from acousticbrain.models import Room, RoomMode

from .room import SPEED_OF_SOUND


class ModesCalculator:

    def axial_modes(
        self,
        room: Room,
        order: int = 4,
    ) -> list[RoomMode]:

        modes = []

        axes = [
            ("Longueur", room.length),
            ("Largeur", room.width),
            ("Hauteur", room.height),
        ]

        for axis_name, dimension in axes:

            for n in range(1, order + 1):

                frequency = (
                    SPEED_OF_SOUND
                    * n
                    / (2 * dimension)
                )

                modes.append(

                    RoomMode(

                        axis=axis_name,

                        order=n,

                        frequency=frequency,

                    )

                )

        modes.sort(key=lambda mode: mode.frequency)

        return modes