from dataclasses import dataclass, field

from acousticbrain.models import Peak


@dataclass
class StereoAnalysis:

    common_peaks: list[tuple[Peak, Peak]] = field(default_factory=list)

    left_only_peaks: list[Peak] = field(default_factory=list)

    right_only_peaks: list[Peak] = field(default_factory=list)

    tolerance_hz: float = 2.0

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

        total = (
            self.common_count
            + self.left_only_count
            + self.right_only_count
        )

        if total == 0:
            return 100.0

        return (
            self.common_count
            / total
        ) * 100.0