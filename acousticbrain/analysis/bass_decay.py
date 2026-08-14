from __future__ import annotations

from statistics import fmean

import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.stats import linregress

from acousticbrain.models import (
    BassDecayBandAnalysis,
    BassDecayChannelAnalysis,
    DecayUsability,
    ImpulseResponse,
)


class BassDecayAnalyzer:
    """Mesure la décroissance basse fréquence d'une impulsion mono-canal."""

    THIRD_OCTAVE_CENTERS_HZ = (
        20.0,
        25.0,
        31.5,
        40.0,
        50.0,
        63.0,
        80.0,
        100.0,
        125.0,
        160.0,
        200.0,
    )
    BAND_EDGE_FACTOR = 2 ** (1 / 6)
    START_LEVEL_DB = -5.0
    END_LEVEL_DB = -25.0
    REQUIRED_DYNAMIC_RANGE_DB = 20.0
    REQUIRED_NOISE_MARGIN_DB = 5.0
    MINIMUM_OBSERVED_DURATION_SECONDS = 0.05
    MINIMUM_REGRESSION_SAMPLES = 20
    MINIMUM_FIT_CORRELATION = 0.90
    METHOD = "THIRD_OCTAVE_ENERGY_DECAY_REGRESSION"

    def analyze(
        self,
        impulse_response: ImpulseResponse,
        *,
        center_frequencies_hz: tuple[float, ...] | None = None,
    ) -> BassDecayChannelAnalysis:
        self._validate(impulse_response)
        centers = (
            self.THIRD_OCTAVE_CENTERS_HZ
            if center_frequencies_hz is None
            else center_frequencies_hz
        )
        bands = [
            self._analyze_band(impulse_response, center)
            for center in centers
            if self._valid_band(center, impulse_response.sample_rate_hz)
        ]
        usable = [
            band for band in bands if band.usability is DecayUsability.USABLE
        ]
        durations = [
            band.observed_duration_seconds
            for band in bands
            if band.observed_duration_seconds is not None
        ]
        covered_range = (
            (bands[0].minimum_frequency_hz, bands[-1].maximum_frequency_hz)
            if bands
            else None
        )
        return BassDecayChannelAnalysis(
            channel=impulse_response.channel,
            band_analyses=bands,
            covered_frequency_range_hz=covered_range,
            maximum_observed_duration_seconds=(
                max(durations) if durations else None
            ),
            usable_band_count=len(usable),
            confidence=(
                fmean(band.confidence for band in usable) if usable else 0.0
            ),
            method=self.METHOD,
        )

    def _analyze_band(self, impulse_response, center):
        minimum = center / self.BAND_EDGE_FACTOR
        maximum = center * self.BAND_EDGE_FACTOR
        unavailable = self._band(
            center,
            minimum,
            maximum,
            usability=DecayUsability.INSUFFICIENT_DURATION,
        )
        try:
            filtered = self._filter(
                impulse_response.samples,
                impulse_response.sample_rate_hz,
                minimum,
                maximum,
            )
        except ValueError:
            return unavailable

        peak_index = (
            impulse_response.peak_index
            if impulse_response.peak_index is not None
            else int(np.argmax(np.abs(filtered)))
        )
        decay = np.asarray(filtered[peak_index:], dtype=float)
        minimum_samples = max(
            self.MINIMUM_REGRESSION_SAMPLES,
            round(
                self.MINIMUM_OBSERVED_DURATION_SECONDS
                * impulse_response.sample_rate_hz
            ),
        )
        if len(decay) < minimum_samples:
            return unavailable

        curve_db, noise_floor_db = self._energy_decay_curve(decay)
        if curve_db is None:
            return self._band(
                center,
                minimum,
                maximum,
                noise_floor_db=noise_floor_db,
                usability=DecayUsability.INSUFFICIENT_DYNAMIC_RANGE,
            )

        available_range = max(0.0, -float(np.min(curve_db)))
        noise_margin = self.END_LEVEL_DB - noise_floor_db
        if noise_margin < self.REQUIRED_NOISE_MARGIN_DB:
            return self._band(
                center,
                minimum,
                maximum,
                observed_decay_range_db=available_range,
                noise_floor_db=noise_floor_db,
                noise_margin_db=noise_margin,
                usability=DecayUsability.NOISE_FLOOR_REACHED,
            )
        if available_range < self.REQUIRED_DYNAMIC_RANGE_DB:
            return self._band(
                center,
                minimum,
                maximum,
                observed_decay_range_db=available_range,
                noise_floor_db=noise_floor_db,
                noise_margin_db=noise_margin,
                usability=DecayUsability.INSUFFICIENT_DYNAMIC_RANGE,
            )

        mask = (curve_db <= self.START_LEVEL_DB) & (
            curve_db >= self.END_LEVEL_DB
        )
        indices = np.flatnonzero(mask)
        if len(indices) < self.MINIMUM_REGRESSION_SAMPLES:
            return self._band(
                center,
                minimum,
                maximum,
                observed_decay_range_db=available_range,
                noise_floor_db=noise_floor_db,
                noise_margin_db=noise_margin,
                usability=DecayUsability.INSUFFICIENT_DURATION,
            )
        time_seconds = indices / impulse_response.sample_rate_hz
        observed_duration = float(time_seconds[-1] - time_seconds[0])
        if observed_duration < self.MINIMUM_OBSERVED_DURATION_SECONDS:
            return self._band(
                center,
                minimum,
                maximum,
                start_level_db=float(curve_db[indices[0]]),
                end_level_db=float(curve_db[indices[-1]]),
                observed_decay_range_db=available_range,
                observed_duration_seconds=observed_duration,
                noise_floor_db=noise_floor_db,
                noise_margin_db=noise_margin,
                usability=DecayUsability.INSUFFICIENT_DURATION,
            )

        regression = linregress(time_seconds, curve_db[indices])
        slope = float(regression.slope)
        correlation = float(regression.rvalue)
        common = dict(
            start_level_db=float(curve_db[indices[0]]),
            end_level_db=float(curve_db[indices[-1]]),
            observed_decay_range_db=float(
                curve_db[indices[0]] - curve_db[indices[-1]]
            ),
            observed_duration_seconds=observed_duration,
            decay_slope_db_per_second=(slope if np.isfinite(slope) else None),
            noise_floor_db=noise_floor_db,
            noise_margin_db=noise_margin,
            fit_correlation=(correlation if np.isfinite(correlation) else None),
        )
        if (
            not np.isfinite(slope)
            or slope >= 0.0
            or not np.isfinite(correlation)
            or abs(correlation) < self.MINIMUM_FIT_CORRELATION
        ):
            return self._band(
                center,
                minimum,
                maximum,
                **common,
                usability=DecayUsability.UNSTABLE_SLOPE,
            )

        decay_time = -60.0 / slope
        confidence = self._confidence(
            abs(correlation), noise_margin, observed_duration
        )
        return self._band(
            center,
            minimum,
            maximum,
            **common,
            estimated_decay_time_seconds=float(decay_time),
            confidence=confidence,
            usability=DecayUsability.USABLE,
        )

    @staticmethod
    def _energy_decay_curve(decay):
        energy = np.square(decay)
        peak_power = float(np.max(energy))
        if peak_power <= 0.0:
            return None, None
        tail_length = max(20, len(energy) // 10)
        noise_power = float(np.mean(energy[-tail_length:]))
        noise_floor_db = BassDecayAnalyzer._db_ratio(
            noise_power, peak_power
        )
        corrected = np.maximum(energy - noise_power, 0.0)
        integrated = np.cumsum(corrected[::-1])[::-1]
        if integrated[0] <= 0.0:
            return None, noise_floor_db
        curve_db = 10.0 * np.log10(
            np.maximum(
                integrated / integrated[0], np.finfo(float).tiny
            )
        )
        return curve_db, noise_floor_db

    @classmethod
    def _confidence(cls, correlation, noise_margin, duration):
        correlation_quality = min(
            1.0,
            max(
                0.0,
                (correlation - cls.MINIMUM_FIT_CORRELATION)
                / (1.0 - cls.MINIMUM_FIT_CORRELATION),
            ),
        )
        noise_quality = min(1.0, max(0.0, noise_margin) / 20.0)
        duration_quality = min(
            1.0,
            duration / (4.0 * cls.MINIMUM_OBSERVED_DURATION_SECONDS),
        )
        return 100.0 * (
            0.5 * correlation_quality
            + 0.3 * noise_quality
            + 0.2 * duration_quality
        )

    @classmethod
    def _band(cls, center, minimum, maximum, **facts):
        return BassDecayBandAnalysis(
            center_frequency_hz=center,
            minimum_frequency_hz=minimum,
            maximum_frequency_hz=maximum,
            method=cls.METHOD,
            **facts,
        )

    @staticmethod
    def _filter(samples, sample_rate_hz, minimum_hz, maximum_hz):
        sos = butter(
            4,
            (minimum_hz, maximum_hz),
            btype="bandpass",
            fs=sample_rate_hz,
            output="sos",
        )
        return sosfiltfilt(sos, np.asarray(samples, dtype=float))

    @classmethod
    def _valid_band(cls, center, sample_rate_hz):
        return (
            center > 0.0
            and center * cls.BAND_EDGE_FACTOR < sample_rate_hz / 2.0
        )

    @staticmethod
    def _db_ratio(numerator, denominator):
        if numerator <= 0.0:
            return float("-inf")
        return float(10.0 * np.log10(numerator / denominator))

    @staticmethod
    def _validate(impulse_response):
        if impulse_response.sample_rate_hz <= 0.0:
            raise ValueError("Impulse response sample rate must be positive.")
        if not impulse_response.samples:
            raise ValueError("Impulse response samples are required.")
        if (
            impulse_response.peak_index is not None
            and not 0
            <= impulse_response.peak_index
            < len(impulse_response.samples)
        ):
            raise ValueError("Impulse response peak index is outside the samples.")
