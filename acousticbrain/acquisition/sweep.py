from dataclasses import dataclass

import numpy as np
from scipy import signal


@dataclass(frozen=True)
class SweepParameters:
    sample_rate_hz: int = 44100
    start_hz: float = 20.0
    end_hz: float = 20000.0
    duration_s: float = 5.0
    level_dbfs: float = -24.0

    def __post_init__(self):
        if self.sample_rate_hz <= 0:
            raise ValueError("Sample rate must be positive.")
        if self.start_hz <= 0 or self.end_hz <= self.start_hz:
            raise ValueError("Sweep frequency bounds must be increasing and positive.")
        if self.duration_s <= 0:
            raise ValueError("Sweep duration must be positive.")
        if self.level_dbfs > 0:
            raise ValueError("Sweep level cannot exceed 0 dBFS.")


def logarithmic_sweep(parameters: SweepParameters) -> np.ndarray:
    samples = int(round(parameters.sample_rate_hz * parameters.duration_s))
    time = np.arange(samples, dtype=float) / parameters.sample_rate_hz
    sweep = signal.chirp(
        time,
        f0=parameters.start_hz,
        f1=parameters.end_hz,
        t1=parameters.duration_s,
        method="logarithmic",
    )
    fade_samples = max(1, int(round(0.01 * parameters.sample_rate_hz)))
    fade = np.sin(np.linspace(0.0, np.pi / 2.0, fade_samples)) ** 2
    sweep[:fade_samples] *= fade
    sweep[-fade_samples:] *= fade[::-1]
    return sweep * (10.0 ** (parameters.level_dbfs / 20.0))
