import math

from acousticbrain.models import (
    Room,
    RoomMode,
    RoomModesAnalysis,
    RoomModeType,
)
from acousticbrain.physics.room import SPEED_OF_SOUND


class RoomModesAnalyzer:
    """Calcule les modes propres à partir de la seule géométrie de salle."""

    def analyze(
        self,
        room: Room,
        *,
        minimum_frequency_hz: float,
        maximum_frequency_hz: float,
        maximum_order: int,
    ) -> RoomModesAnalysis:
        self._validate_bounds(
            room,
            minimum_frequency_hz,
            maximum_frequency_hz,
            maximum_order,
        )
        modes: list[RoomMode] = []
        modal_indices: set[tuple[int, int, int]] = set()

        for order_x in range(maximum_order + 1):
            for order_y in range(maximum_order + 1):
                for order_z in range(maximum_order + 1):
                    indices = (order_x, order_y, order_z)
                    if indices == (0, 0, 0) or indices in modal_indices:
                        continue
                    modal_indices.add(indices)

                    frequency = self._frequency(room, *indices)
                    if not minimum_frequency_hz <= frequency <= maximum_frequency_hz:
                        continue

                    modes.append(
                        RoomMode(
                            mode_type=self._mode_type(indices),
                            order_x=order_x,
                            order_y=order_y,
                            order_z=order_z,
                            frequency=frequency,
                            axes=self._axes(indices),
                        )
                    )

        modes.sort(key=lambda mode: mode.frequency)
        axial_modes = [
            mode for mode in modes if mode.mode_type is RoomModeType.AXIAL
        ]
        tangential_modes = [
            mode for mode in modes if mode.mode_type is RoomModeType.TANGENTIAL
        ]
        oblique_modes = [
            mode for mode in modes if mode.mode_type is RoomModeType.OBLIQUE
        ]

        return RoomModesAnalysis(
            modes=modes,
            axial_modes=axial_modes,
            tangential_modes=tangential_modes,
            oblique_modes=oblique_modes,
            minimum_frequency_hz=minimum_frequency_hz,
            maximum_frequency_hz=maximum_frequency_hz,
            axial_count=len(axial_modes),
            tangential_count=len(tangential_modes),
            oblique_count=len(oblique_modes),
            total_count=len(modes),
            confidence=100.0,
        )

    @staticmethod
    def _frequency(room: Room, order_x: int, order_y: int, order_z: int) -> float:
        indices = (order_x, order_y, order_z)
        if sum(index > 0 for index in indices) == 1:
            order, dimension = next(
                (order, dimension)
                for order, dimension in zip(
                    indices,
                    (room.length, room.width, room.height),
                )
                if order > 0
            )
            return SPEED_OF_SOUND * order / (2 * dimension)

        return SPEED_OF_SOUND / 2.0 * math.sqrt(
            (order_x / room.length) ** 2
            + (order_y / room.width) ** 2
            + (order_z / room.height) ** 2
        )

    @staticmethod
    def _mode_type(indices: tuple[int, int, int]) -> RoomModeType:
        nonzero_count = sum(index > 0 for index in indices)
        return {
            1: RoomModeType.AXIAL,
            2: RoomModeType.TANGENTIAL,
            3: RoomModeType.OBLIQUE,
        }[nonzero_count]

    @staticmethod
    def _axes(indices: tuple[int, int, int]) -> tuple[str, ...]:
        return tuple(
            axis
            for axis, index in zip(
                ("Longueur", "Largeur", "Hauteur"),
                indices,
            )
            if index > 0
        )

    @staticmethod
    def _validate_bounds(
        room: Room,
        minimum_frequency_hz: float,
        maximum_frequency_hz: float,
        maximum_order: int,
    ) -> None:
        if min(room.length, room.width, room.height) <= 0:
            raise ValueError("Room dimensions must be greater than zero.")
        if minimum_frequency_hz < 0:
            raise ValueError("Minimum frequency must be non-negative.")
        if maximum_frequency_hz < minimum_frequency_hz:
            raise ValueError("Maximum frequency must not be below minimum frequency.")
        if maximum_order < 1:
            raise ValueError("Maximum modal order must be at least one.")
