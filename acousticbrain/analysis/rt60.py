from __future__ import annotations

from dataclasses import replace

import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.stats import linregress

from acousticbrain.models import (
    ImpulseResponse,
    RT60BandAnalysis,
    RT60ChannelAnalysis,
)


class RT60Analyzer:
    """Estime le RT60 mono-canal à partir d'une réponse impulsionnelle."""

    THIRD_OCTAVE_CENTERS_HZ = (
        50.0,
        63.0,
        80.0,
        100.0,
        125.0,
        160.0,
        200.0,
        250.0,
        315.0,
        400.0,
        500.0,
        630.0,
        800.0,
        1000.0,
        1250.0,
        1600.0,
        2000.0,
        2500.0,
        3150.0,
        4000.0,
        5000.0,
        6300.0,
        8000.0,
        10000.0,
    )
    BAND_EDGE_FACTOR = 2 ** (1 / 6)
    MINIMUM_REGRESSION_SAMPLES = 20
    NOISE_MARGIN_DB = 5.0

    def analyze(
        self,
        impulse_response: ImpulseResponse,
        *,
        center_frequencies_hz: tuple[float, ...] | None = None,
    ) -> RT60ChannelAnalysis:
        self._validate(impulse_response)
        centers = (
            self.THIRD_OCTAVE_CENTERS_HZ
            if center_frequencies_hz is None
            else center_frequencies_hz
        )
        band_analyses = [
            self._analyze_band(impulse_response, center)
            for center in centers
            if self._valid_band(center, impulse_response.sample_rate_hz)
        ]
        available = [
            band.rt60_seconds
            for band in band_analyses
            if band.rt60_seconds is not None
        ]
        confidences = [
            band.confidence
            for band in band_analyses
            if band.rt60_seconds is not None
        ]

        return RT60ChannelAnalysis(
            channel=impulse_response.channel,
            band_analyses=band_analyses,
            broadband_rt60_seconds=(
                float(np.median(available)) if available else None
            ),
            minimum_rt60_seconds=min(available) if available else None,
            maximum_rt60_seconds=max(available) if available else None,
            confidence=float(np.mean(confidences)) if confidences else 0.0,
        )

    def _analyze_band(
        self,
        impulse_response: ImpulseResponse,
        center_frequency_hz: float,
    ) -> RT60BandAnalysis:
        minimum_frequency_hz = center_frequency_hz / self.BAND_EDGE_FACTOR
        maximum_frequency_hz = center_frequency_hz * self.BAND_EDGE_FACTOR
        unavailable = self._unavailable_band(
            center_frequency_hz,
            minimum_frequency_hz,
            maximum_frequency_hz,
        )

        try:
            filtered = self._filter(
                impulse_response.samples,
                impulse_response.sample_rate_hz,
                minimum_frequency_hz,
                maximum_frequency_hz,
            )
        except ValueError:
            return unavailable

        peak_index = (
            impulse_response.peak_index
            if impulse_response.peak_index is not None
            else int(np.argmax(np.abs(filtered)))
        )
        decay = filtered[peak_index:]
        if len(decay) < self.MINIMUM_REGRESSION_SAMPLES:
            return unavailable

        energy = np.square(decay)
        tail_length = max(self.MINIMUM_REGRESSION_SAMPLES, len(energy) // 10)
        noise_power = float(np.mean(energy[-tail_length:]))
        peak_power = float(np.max(energy))
        if peak_power <= 0:
            return unavailable

        noise_floor_db = self._db_ratio(noise_power, peak_power)
        corrected_energy = np.maximum(energy - noise_power, 0.0)
        integrated = np.cumsum(corrected_energy[::-1])[::-1]
        if integrated[0] <= 0:
            return unavailable

        decay_db = 10.0 * np.log10(
            np.maximum(integrated / integrated[0], np.finfo(float).tiny)
        )
        time_seconds = np.arange(len(decay_db)) / impulse_response.sample_rate_hz

        edt = self._estimate(
            time_seconds,
            decay_db,
            noise_floor_db,
            upper_db=0.0,
            lower_db=-10.0,
        )
        t20 = self._estimate(
            time_seconds,
            decay_db,
            noise_floor_db,
            upper_db=-5.0,
            lower_db=-25.0,
        )
        t30 = self._estimate(
            time_seconds,
            decay_db,
            noise_floor_db,
            upper_db=-5.0,
            lower_db=-35.0,
        )
        selected_name, selected, decay_range = self._select(edt, t20, t30)
        if selected is None:
            return replace(unavailable, noise_floor_db=noise_floor_db)

        rt60_seconds, correlation = selected
        confidence = self._confidence(
            selected_name,
            correlation,
            noise_floor_db,
            decay_range[1],
        )

        return RT60BandAnalysis(
            center_frequency_hz=center_frequency_hz,
            minimum_frequency_hz=minimum_frequency_hz,
            maximum_frequency_hz=maximum_frequency_hz,
            rt60_seconds=rt60_seconds,
            decay_range_db=decay_range,
            fit_correlation=correlation,
            confidence=confidence,
            edt_seconds=edt[0] if edt else None,
            t20_seconds=t20[0] if t20 else None,
            t30_seconds=t30[0] if t30 else None,
            selected_estimate=selected_name,
            noise_floor_db=noise_floor_db,
        )

    @classmethod
    def _estimate(
        cls,
        time_seconds,
        decay_db,
        noise_floor_db,
        *,
        upper_db,
        lower_db,
    ):
        if noise_floor_db > lower_db - cls.NOISE_MARGIN_DB:
            return None
        if float(np.min(decay_db)) > lower_db:
            return None

        mask = (decay_db <= upper_db) & (decay_db >= lower_db)
        if int(np.count_nonzero(mask)) < cls.MINIMUM_REGRESSION_SAMPLES:
            return None

        regression = linregress(time_seconds[mask], decay_db[mask])
        if regression.slope >= 0 or not np.isfinite(regression.slope):
            return None

        rt60_seconds = -60.0 / regression.slope
        if not np.isfinite(rt60_seconds) or rt60_seconds <= 0:
            return None
        return float(rt60_seconds), abs(float(regression.rvalue))

    @staticmethod
    def _select(edt, t20, t30):
        if t30 is not None:
            return "T30", t30, (-5.0, -35.0)
        if t20 is not None:
            return "T20", t20, (-5.0, -25.0)
        if edt is not None:
            return "EDT", edt, (0.0, -10.0)
        return None, None, (0.0, 0.0)

    @staticmethod
    def _confidence(method, correlation, noise_floor_db, lower_db):
        range_weight = {"EDT": 0.5, "T20": 0.75, "T30": 1.0}[method]
        noise_margin = max(0.0, lower_db - noise_floor_db)
        noise_weight = min(1.0, noise_margin / 20.0)
        return 100.0 * range_weight * correlation * noise_weight

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
    def _valid_band(cls, center_frequency_hz, sample_rate_hz):
        return (
            center_frequency_hz > 0
            and center_frequency_hz * cls.BAND_EDGE_FACTOR < sample_rate_hz / 2
        )

    @staticmethod
    def _unavailable_band(center, minimum, maximum):
        return RT60BandAnalysis(
            center_frequency_hz=center,
            minimum_frequency_hz=minimum,
            maximum_frequency_hz=maximum,
            rt60_seconds=None,
            decay_range_db=(0.0, 0.0),
            fit_correlation=None,
            confidence=0.0,
        )

    @staticmethod
    def _db_ratio(numerator, denominator):
        if numerator <= 0:
            return float("-inf")
        return float(10.0 * np.log10(numerator / denominator))

    @staticmethod
    def _validate(impulse_response):
        if impulse_response.sample_rate_hz <= 0:
            raise ValueError("Impulse response sample rate must be positive.")
        if not impulse_response.samples:
            raise ValueError("Impulse response samples are required.")
        if (
            impulse_response.peak_index is not None
            and not 0 <= impulse_response.peak_index < len(impulse_response.samples)
        ):
            raise ValueError("Impulse response peak index is outside the samples.")
