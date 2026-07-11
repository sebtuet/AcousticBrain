from dataclasses import dataclass

from .room_mode_type import RoomModeType


@dataclass(init=False)
class RoomMode:
    mode_type: RoomModeType
    order_x: int
    order_y: int
    order_z: int
    frequency: float
    axes: tuple[str, ...]

    def __init__(
        self,
        axis: str | None = None,
        order: int | None = None,
        frequency: float = 0.0,
        *,
        mode_type: RoomModeType = RoomModeType.AXIAL,
        order_x: int = 0,
        order_y: int = 0,
        order_z: int = 0,
        axes: tuple[str, ...] = (),
    ):
        """Construit le nouveau contrat ou adapte l'ancien couple axe/ordre."""

        if axis is not None:
            legacy_orders = {
                "Longueur": (order or 0, 0, 0),
                "Largeur": (0, order or 0, 0),
                "Hauteur": (0, 0, order or 0),
            }
            order_x, order_y, order_z = legacy_orders[axis]
            axes = (axis,)
            mode_type = RoomModeType.AXIAL

        self.mode_type = mode_type
        self.order_x = order_x
        self.order_y = order_y
        self.order_z = order_z
        self.frequency = frequency
        self.axes = axes

    @property
    def axis(self) -> str:
        """Compatibilité temporaire avec les consommateurs axiaux v0.11.0."""

        return self.axes[0] if len(self.axes) == 1 else " / ".join(self.axes)

    @property
    def order(self) -> int:
        """Compatibilité temporaire avec l'ordre axial historique."""

        return max(self.order_x, self.order_y, self.order_z)

