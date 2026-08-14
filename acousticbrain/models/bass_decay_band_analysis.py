from dataclasses import dataclass

from .decay_usability import DecayUsability


@dataclass(frozen=True)
class BassDecayBandAnalysis:
    """Faits de décroissance basse fréquence pour une bande."""

    center_frequency_hz: float
    minimum_frequency_hz: float
    maximum_frequency_hz: float
    start_level_db: float | None = None
    end_level_db: float | None = None
    observed_decay_range_db: float | None = None
    observed_duration_seconds: float | None = None
    decay_slope_db_per_second: float | None = None
    estimated_decay_time_seconds: float | None = None
    noise_floor_db: float | None = None
    noise_margin_db: float | None = None
    fit_correlation: float | None = None
    confidence: float = 0.0
    method: str = ""
    usability: DecayUsability = DecayUsability.INSUFFICIENT_DYNAMIC_RANGE

    def __post_init__(self):
        if not (
            self.minimum_frequency_hz
            <= self.center_frequency_hz
            <= self.maximum_frequency_hz
        ):
            raise ValueError("Band bounds must contain the center frequency.")
        if self.minimum_frequency_hz >= self.maximum_frequency_hz:
            raise ValueError("Band frequency bounds must be ordered.")
        if (
            self.observed_decay_range_db is not None
            and self.observed_decay_range_db < 0.0
        ):
            raise ValueError("Observed decay range cannot be negative.")
        if (
            self.observed_duration_seconds is not None
            and self.observed_duration_seconds < 0.0
        ):
            raise ValueError("Observed duration cannot be negative.")
        if self.fit_correlation is not None and not (
            -1.0 <= self.fit_correlation <= 1.0
        ):
            raise ValueError("Fit correlation must be between -1 and 1.")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Confidence must be between 0 and 100.")
        self._validate_exploitability()

    def _validate_exploitability(self):
        if self.usability is not DecayUsability.USABLE:
            if self.estimated_decay_time_seconds is not None:
                raise ValueError(
                    "An unusable band cannot expose an estimated decay time."
                )
            return

        required = (
            self.start_level_db,
            self.end_level_db,
            self.observed_decay_range_db,
            self.observed_duration_seconds,
            self.decay_slope_db_per_second,
            self.estimated_decay_time_seconds,
            self.noise_floor_db,
            self.noise_margin_db,
            self.fit_correlation,
        )
        if any(value is None for value in required):
            raise ValueError("A usable band requires all decay facts.")
        if self.observed_decay_range_db <= 0.0:
            raise ValueError("A usable band requires a positive dynamic range.")
        if self.observed_duration_seconds <= 0.0:
            raise ValueError("A usable band requires a positive duration.")
        if self.decay_slope_db_per_second >= 0.0:
            raise ValueError("A usable decay slope must be negative.")
        if self.estimated_decay_time_seconds <= 0.0:
            raise ValueError("Estimated decay time must be positive.")
