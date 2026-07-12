from acousticbrain.models import RoomGeometry, RoomMode

from .room import SPEED_OF_SOUND


class ModesCalculator:

    def axial_modes(
        self,
        geometry: RoomGeometry,
        order: int = 4,
    ) -> list[RoomMode]:

        if not isinstance(geometry, RoomGeometry):
            raise TypeError("ModesCalculator requires RoomGeometry.")
        dimensions = geometry.dimensions
        modes = []

        axes = [
            ("Longueur", dimensions.length_m),
            ("Largeur", dimensions.width_m),
            ("Hauteur", dimensions.height_m),
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
