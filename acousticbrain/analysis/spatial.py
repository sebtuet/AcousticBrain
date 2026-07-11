from __future__ import annotations

from statistics import fmean

import numpy as np
from scipy.signal import butter, correlate, correlation_lags, sosfiltfilt

from acousticbrain.models import (
    ImpulseResponse,
    SpatialBandAnalysis,
    SpatialChannelPairAnalysis,
    SpatialMeasurementType,
)


class SpatialAnalyzer:
    """Calcule des faits techniques pour une paire de réponses impulsionnelles."""

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
    DEFAULT_ANALYSIS_WINDOW_MS = 100.0
    DEFAULT_MAXIMUM_CORRELATION_DELAY_MS = 10.0
    MAXIMUM_INTERAURAL_DELAY_MS = 1.0
    DIRECT_SEARCH_TOLERANCE_MS = 5.0
    METHOD = "THIRD_OCTAVE_PAIR_CROSS_CORRELATION"
    BROADBAND_METHOD = "BROADBAND_PAIR_CROSS_CORRELATION"
    MINIMUM_ENERGY = 1e-20

    def analyze(
        self,
        first: ImpulseResponse,
        second: ImpulseResponse,
        measurement_type: SpatialMeasurementType,
        *,
        center_frequencies_hz: tuple[float, ...] | None = None,
        analysis_window_ms: float = DEFAULT_ANALYSIS_WINDOW_MS,
        maximum_correlation_delay_ms: float = (
            DEFAULT_MAXIMUM_CORRELATION_DELAY_MS
        ),
    ) -> SpatialChannelPairAnalysis:
        self._validate(
            first,
            second,
            measurement_type,
            analysis_window_ms,
            maximum_correlation_delay_ms,
        )
        centers = (
            self.THIRD_OCTAVE_CENTERS_HZ
            if center_frequencies_hz is None
            else center_frequencies_hz
        )
        bands = [
            self._analyze_band(
                first,
                second,
                measurement_type,
                center,
                analysis_window_ms,
                maximum_correlation_delay_ms,
            )
            for center in centers
            if self._valid_band(center, first.sample_rate_hz)
        ]
        broadband = self._pair_facts(
            np.asarray(first.samples, dtype=float),
            np.asarray(second.samples, dtype=float),
            first,
            second,
            analysis_window_ms,
            maximum_correlation_delay_ms,
        )

        return SpatialChannelPairAnalysis(
            measurement_type=measurement_type,
            bands=bands,
            broadband_level_difference_db=broadband[0],
            broadband_time_difference_ms=broadband[1],
            broadband_cross_correlation=broadband[2],
            confidence=(
                fmean(band.confidence for band in bands)
                if bands
                else broadband[4]
            ),
            method=self.BROADBAND_METHOD,
        )

    def _analyze_band(
        self,
        first,
        second,
        measurement_type,
        center_frequency_hz,
        analysis_window_ms,
        maximum_correlation_delay_ms,
    ):
        unavailable = self._unavailable_band(center_frequency_hz, measurement_type)
        minimum_hz = center_frequency_hz / self.BAND_EDGE_FACTOR
        maximum_hz = center_frequency_hz * self.BAND_EDGE_FACTOR
        try:
            first_filtered = self._filter(
                first.samples,
                first.sample_rate_hz,
                minimum_hz,
                maximum_hz,
            )
            second_filtered = self._filter(
                second.samples,
                second.sample_rate_hz,
                minimum_hz,
                maximum_hz,
            )
        except ValueError:
            return unavailable

        level, time, coefficient, delay, confidence = self._pair_facts(
            first_filtered,
            second_filtered,
            first,
            second,
            analysis_window_ms,
            maximum_correlation_delay_ms,
        )
        if level is None:
            return unavailable
        binaural = measurement_type is SpatialMeasurementType.BINAURAL_PAIR
        interaural_correlation, interaural_delay = (
            self._interaural_correlation(
                first_filtered,
                second_filtered,
                first,
                second,
                analysis_window_ms,
            )
            if binaural
            else (None, None)
        )
        return SpatialBandAnalysis(
            center_frequency_hz=center_frequency_hz,
            level_difference_db=level,
            time_difference_ms=time,
            cross_correlation=coefficient,
            correlation_delay_ms=delay,
            interaural_level_difference_db=level if binaural else None,
            interaural_time_difference_ms=interaural_delay,
            iacc=interaural_correlation,
            measurement_type=measurement_type,
            confidence=confidence,
            method=self.METHOD,
        )

    @classmethod
    def _interaural_correlation(
        cls,
        first_samples,
        second_samples,
        first_response,
        second_response,
        analysis_window_ms,
    ):
        start = min(
            cls._direct_index(first_samples, first_response),
            cls._direct_index(second_samples, second_response),
        )
        length = max(
            1,
            round(analysis_window_ms * first_response.sample_rate_hz / 1000.0),
        )
        return cls._cross_correlation(
            cls._window(first_samples, start, length),
            cls._window(second_samples, start, length),
            first_response.sample_rate_hz,
            cls.MAXIMUM_INTERAURAL_DELAY_MS,
        )

    @classmethod
    def _pair_facts(
        cls,
        first_samples,
        second_samples,
        first_response,
        second_response,
        analysis_window_ms,
        maximum_correlation_delay_ms,
    ):
        first_direct = cls._direct_index(first_samples, first_response)
        second_direct = cls._direct_index(second_samples, second_response)
        time_difference_ms = cls._direct_time_difference_ms(
            first_response,
            second_response,
            first_direct,
            second_direct,
        )
        start = min(first_direct, second_direct)
        length = max(
            1,
            round(analysis_window_ms * first_response.sample_rate_hz / 1000.0),
        )
        first_window = cls._window(first_samples, start, length)
        second_window = cls._window(second_samples, start, length)
        first_energy = float(np.sum(np.square(first_window)))
        second_energy = float(np.sum(np.square(second_window)))
        if first_energy <= cls.MINIMUM_ENERGY or second_energy <= cls.MINIMUM_ENERGY:
            return None, time_difference_ms, None, None, 0.0

        level_difference_db = 10.0 * np.log10(first_energy / second_energy)
        coefficient, delay_ms = cls._cross_correlation(
            first_window,
            second_window,
            first_response.sample_rate_hz,
            maximum_correlation_delay_ms,
        )
        confidence = cls._confidence(
            first_samples,
            second_samples,
            first_energy,
            second_energy,
            coefficient,
        )
        return (
            float(level_difference_db),
            time_difference_ms,
            coefficient,
            delay_ms,
            confidence,
        )

    @staticmethod
    def _window(samples, start, length):
        result = np.zeros(length, dtype=float)
        available = samples[start : min(len(samples), start + length)]
        result[: len(available)] = available
        return result

    @staticmethod
    def _cross_correlation(first, second, sample_rate_hz, maximum_delay_ms):
        first_centered = first - np.mean(first)
        second_centered = second - np.mean(second)
        denominator = float(np.linalg.norm(first_centered) * np.linalg.norm(second_centered))
        if denominator <= 0:
            return None, None
        values = correlate(first_centered, second_centered, mode="full") / denominator
        lags = correlation_lags(len(first_centered), len(second_centered), mode="full")
        maximum_lag = round(maximum_delay_ms * sample_rate_hz / 1000.0)
        mask = np.abs(lags) <= maximum_lag
        if not np.any(mask):
            return None, None
        candidates = np.flatnonzero(mask)
        index = candidates[int(np.argmax(np.abs(values[mask])))]
        return (
            abs(float(values[index])),
            float(1000.0 * lags[index] / sample_rate_hz),
        )

    @classmethod
    def _direct_index(cls, samples, response):
        global_index = int(np.argmax(np.abs(samples)))
        if response.peak_index is None:
            return global_index
        radius = max(
            1,
            round(cls.DIRECT_SEARCH_TOLERANCE_MS * response.sample_rate_hz / 1000.0),
        )
        minimum = max(0, response.peak_index - radius)
        maximum = min(len(samples), response.peak_index + radius + 1)
        local_index = minimum + int(np.argmax(np.abs(samples[minimum:maximum])))
        return local_index

    @staticmethod
    def _direct_time_difference_ms(first, second, first_index, second_index):
        first_start = (
            first.start_time_s
            if first.start_time_s is not None
            else first.time_offset_seconds
        )
        second_start = (
            second.start_time_s
            if second.start_time_s is not None
            else second.time_offset_seconds
        )
        first_time = first_start + first_index / first.sample_rate_hz
        second_time = second_start + second_index / second.sample_rate_hz
        return float(1000.0 * (first_time - second_time))

    @classmethod
    def _confidence(
        cls,
        first_samples,
        second_samples,
        first_energy,
        second_energy,
        coefficient,
    ):
        if coefficient is None:
            return 0.0
        first_noise = cls._tail_power(first_samples)
        second_noise = cls._tail_power(second_samples)
        first_mean = first_energy / len(first_samples)
        second_mean = second_energy / len(second_samples)
        noise_ratios = [
            mean / noise
            for mean, noise in (
                (first_mean, first_noise),
                (second_mean, second_noise),
            )
            if noise > 0
        ]
        if not noise_ratios:
            noise_quality = 1.0
        else:
            snr_db = min(10.0 * np.log10(ratio) for ratio in noise_ratios)
            noise_quality = min(1.0, max(0.0, snr_db) / 40.0)
        return 100.0 * (0.6 * coefficient + 0.4 * noise_quality)

    @staticmethod
    def _tail_power(samples):
        tail_length = max(1, len(samples) // 10)
        return float(np.mean(np.square(samples[-tail_length:])))

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
    def _unavailable_band(center, measurement_type):
        return SpatialBandAnalysis(
            center_frequency_hz=center,
            level_difference_db=None,
            time_difference_ms=None,
            cross_correlation=None,
            correlation_delay_ms=None,
            interaural_level_difference_db=None,
            interaural_time_difference_ms=None,
            iacc=None,
            measurement_type=measurement_type,
            confidence=0.0,
            method="",
        )

    @staticmethod
    def _validate(first, second, measurement_type, window_ms, maximum_delay_ms):
        if not isinstance(measurement_type, SpatialMeasurementType):
            raise ValueError("A spatial measurement type is required.")
        if first.sample_rate_hz <= 0 or second.sample_rate_hz <= 0:
            raise ValueError("Impulse response sample rates must be positive.")
        if first.sample_rate_hz != second.sample_rate_hz:
            raise ValueError("Spatial pair sample rates must match.")
        if not first.samples or not second.samples:
            raise ValueError("Two impulse response sample sets are required.")
        if first.channel is second.channel:
            raise ValueError("Spatial pair channels must be distinct.")
        if window_ms <= 0 or maximum_delay_ms <= 0:
            raise ValueError("Spatial analysis windows must be positive.")
        for response in (first, second):
            if (
                response.peak_index is not None
                and not 0 <= response.peak_index < len(response.samples)
            ):
                raise ValueError("Impulse response peak index is outside the samples.")
