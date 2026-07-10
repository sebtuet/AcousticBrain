import math

from acousticbrain.models import (
    Room,
    RoomProperties,
)


class RoomAcoustics:

    def calculate(

        self,

        room: Room,

        rt60: float = 0.30,

    ) -> RoomProperties:

        volume = (
            room.length
            * room.width
            * room.height
        )

        floor_area = (
            room.length
            * room.width
        )

        total_area = (

            2 * room.length * room.width

            + 2 * room.length * room.height

            + 2 * room.width * room.height

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
        