from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class MicrophoneCalibration:
    path: Path
    frequency_hz: np.ndarray
    correction_db: np.ndarray

    def correction_for(self, frequency_hz):
        if len(self.frequency_hz) == 0:
            return np.zeros_like(frequency_hz, dtype=float)
        return np.interp(
            frequency_hz,
            self.frequency_hz,
            self.correction_db,
            left=float(self.correction_db[0]),
            right=float(self.correction_db[-1]),
        )


def load_umik_calibration(path) -> MicrophoneCalibration:
    path = Path(path)
    frequencies = []
    corrections = []
    with path.open("r", encoding="utf-8", errors="ignore") as stream:
        for raw_line in stream:
            line = raw_line.strip()
            if not line or line.startswith(("#", "*")):
                continue
            parts = line.replace(",", ".").split()
            if len(parts) < 2:
                continue
            try:
                frequency = float(parts[0])
                correction = float(parts[1])
            except ValueError:
                continue
            if frequency > 0:
                frequencies.append(frequency)
                corrections.append(correction)
    if not frequencies:
        raise ValueError(f"Calibration file has no usable frequency data: {path}")
    order = np.argsort(frequencies)
    return MicrophoneCalibration(
        path=path,
        frequency_hz=np.asarray(frequencies, dtype=float)[order],
        correction_db=np.asarray(corrections, dtype=float)[order],
    )
