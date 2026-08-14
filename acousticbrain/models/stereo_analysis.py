from dataclasses import dataclass, field

from acousticbrain.models import Peak
from .room_mode import RoomMode


@dataclass
class StereoAnalysis:

    common_peaks: list[tuple[Peak, Peak]] = field(default_factory=list)

    left_only_peaks: list[Peak] = field(default_factory=list)

    right_only_peaks: list[Peak] = field(default_factory=list)

    tolerance_hz: float = 2.0

    relative_tolerance: float = 0.02

    maximum_tolerance_hz: float = 30.0

    weight_power: float = 2.0

    common_modes: list[RoomMode] = field(default_factory=list)

    left_only_modes: list[RoomMode] = field(default_factory=list)

    right_only_modes: list[RoomMode] = field(default_factory=list)

    balance_low: float | None = None

    balance_mid: float | None = None

    balance_high: float | None = None

    @property
    def common_count(self) -> int:

        return len(self.common_peaks)

    @property
    def left_only_count(self) -> int:

        return len(self.left_only_peaks)

    @property
    def right_only_count(self) -> int:

        return len(self.right_only_peaks)

    @property
    def symmetry_score(self) -> float:

        common_weight = sum(
            min(left.prominence, right.prominence) ** self.weight_power
            for left, right in self.common_peaks
        )
        unmatched_weight = sum(
            peak.prominence ** self.weight_power
            for peak in self.left_only_peaks + self.right_only_peaks
        )
        total = common_weight + unmatched_weight

        if total == 0:
            return 100.0

        return (
            common_weight / total
        ) * 100.0
