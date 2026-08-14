import math

from acousticbrain.models import (
    RoomGeometry,
    RoomProperties,
)


class RoomAcoustics:

    def calculate(

        self,

        geometry: RoomGeometry,

        rt60: float = 0.30,

    ) -> RoomProperties:

        if not isinstance(geometry, RoomGeometry):
            raise TypeError("RoomAcoustics requires RoomGeometry.")
        dimensions = geometry.dimensions

        volume = (
            dimensions.length_m
            * dimensions.width_m
            * dimensions.height_m
        )

        floor_area = (
            dimensions.length_m
            * dimensions.width_m
        )

        total_area = (

            2 * dimensions.length_m * dimensions.width_m

            + 2 * dimensions.length_m * dimensions.height_m

            + 2 * dimensions.width_m * dimensions.height_m

        )

        schroeder = (

            2000

            * math.sqrt(rt60 / volume)

        )

        return RoomProperties(

            volume=volume,

            floor_area=floor_area,

            total_area=total_area,

            schroeder_frequency=schroeder,

        )
