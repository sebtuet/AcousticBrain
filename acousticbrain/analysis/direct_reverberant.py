from __future__ import annotations

from statistics import fmean

import numpy as np
from scipy.signal import butter, sosfiltfilt

from acousticbrain.models import (
    DirectReverberantBandAnalysis,
    DirectReverberantChannelAnalysis,
    EnergyWindowAnalysis,
    ImpulseResponse,
)


class DirectReverberantAnalyzer:
    """Intègre les énergies D/R mono-canal dans des fenêtres explicites."""

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
    DEFAULT_WINDOW_START_MS = 0.0
    DEFAULT_DIRECT_END_MS = 5.0
    DEFAULT_EARLY_END_MS = 50.0
    DIRECT_SEARCH_TOLERANCE_MS = 1.0
    MINIMUM_ENERGY = 1e-20
    MINIMUM_RELATIVE_ENERGY = 1e-12
    METHOD = "THIRD_OCTAVE_ENERGY_WINDOWS"
    BROADBAND_METHOD = "BROADBAND_ENERGY_WINDOWS"

    def analyze(
        self,
        impulse_response: ImpulseResponse,
        *,
        center_frequencies_hz: tuple[float, ...] | None = None,
        window_start_ms: float = DEFAULT_WINDOW_START_MS,
        direct_end_ms: float = DEFAULT_DIRECT_END_MS,
        early_end_ms: float = DEFAULT_EARLY_END_MS,
        analysis_end_ms: float | None = None,
    ) -> DirectReverberantChannelAnalysis:
        self._validate(
            impulse_response,
            window_start_ms,
            direct_end_ms,
            early_end_ms,
            analysis_end_ms,
        )
        centers = (
            self.THIRD_OCTAVE_CENTERS_HZ
            if center_frequencies_hz is None
            else center_frequencies_hz
        )
        bands = [
            self._analyze_band(
                impulse_response,
                center,
                window_start_ms,
                direct_end_ms,
                early_end_ms,
                analysis_end_ms,
            )
            for center in centers
            if self._valid_band(center, impulse_response.sample_rate_hz)
        ]
        broadband = self._energy_facts(
            np.asarray(impulse_response.samples, dtype=float),
            impulse_response,
            window_start_ms,
            direct_end_ms,
            early_end_ms,
            analysis_end_ms,
            self.BROADBAND_METHOD,
        )
        confidences = [
            band.confidence
            for band in bands
            if band.direct_to_reverberant_db is not None
        ]

        return DirectReverberantChannelAnalysis(
            channel=impulse_response.channel,
            band_analyses=bands,
            broadband_direct_window=broadband[0],
            broadband_early_window=broadband[1],
            broadband_late_window=broadband[2],
            broadband_total_window=broadband[3],
            broadband_direct_to_reverberant_db=broadband[4],
            window_start_ms=window_start_ms,
            direct_end_ms=direct_end_ms,
            early_end_ms=early_end_ms,
            analysis_end_ms=analysis_end_ms,
            confidence=(
                fmean(confidences) if confidences else broadband[5]
            ),
            method=self.BROADBAND_METHOD,
        )

    def _analyze_band(
        self,
        impulse_response,
        center,
        window_start_ms,
        direct_end_ms,
        early_end_ms,
        analysis_end_ms,
    ):
        try:
            filtered = self._filter(
                impulse_response.samples,
                impulse_response.sample_rate_hz,
                center / self.BAND_EDGE_FACTOR,
                center * self.BAND_EDGE_FACTOR,
            )
        except ValueError:
            return self._unavailable_band(
                center,
                window_start_ms,
                direct_end_ms,
                early_end_ms,
                analysis_end_ms,
            )
        facts = self._energy_facts(
            filtered,
            impulse_response,
            window_start_ms,
            direct_end_ms,
            early_end_ms,
            analysis_end_ms,
            self.METHOD,
        )
        return DirectReverberantBandAnalysis(
            center_frequency_hz=center,
            direct_window=facts[0],
            early_window=facts[1],
            late_window=facts[2],
            total_window=facts[3],
            direct_to_reverberant_db=facts[4],
            confidence=facts[5],
            method=self.METHOD,
        )

    @classmethod
    def _energy_facts(
        cls,
        samples,
        impulse_response,
        window_start_ms,
        direct_end_ms,
        early_end_ms,
        analysis_end_ms,
        method,
    ):
        direct_index = cls._direct_index(samples, impulse_response)
        bounds = {
            "DIRECT": (window_start_ms, direct_end_ms),
            "EARLY": (direct_end_ms, early_end_ms),
            "LATE": (early_end_ms, analysis_end_ms),
            "TOTAL": (window_start_ms, analysis_end_ms),
        }
        energies = {
            name: cls._integrated_energy(
                samples,
                direct_index,
                impulse_response.sample_rate_hz,
                start_ms,
                end_ms,
            )
            for name, (start_ms, end_ms) in bounds.items()
        }
        total = energies["TOTAL"]
        if total <= cls.MINIMUM_ENERGY:
            windows = tuple(
                cls._window(name, *bounds[name], None, None, 0.0, method)
                for name in ("DIRECT", "EARLY", "LATE", "TOTAL")
            )
            return *windows, None, 0.0

        confidence = cls._confidence(samples, energies, total)
        windows = tuple(
            cls._window(
                name,
                *bounds[name],
                energies[name],
                cls._relative_db(energies[name], total),
                confidence,
                method,
            )
            for name in ("DIRECT", "EARLY", "LATE", "TOTAL")
        )
        direct = energies["DIRECT"]
        reverberant = energies["EARLY"] + energies["LATE"]
        minimum = total * cls.MINIMUM_RELATIVE_ENERGY
        ratio = (
            float(10.0 * np.log10(direct / reverberant))
            if direct > minimum and reverberant > minimum
            else None
        )
        return *windows, ratio, confidence

    @staticmethod
    def _integrated_energy(samples, direct_index, sample_rate_hz, start_ms, end_ms):
        start = direct_index + round(start_ms * sample_rate_hz / 1000.0)
        end = (
            len(samples)
            if end_ms is None
            else direct_index + round(end_ms * sample_rate_hz / 1000.0)
        )
        start = min(len(samples), max(0, start))
        end = min(len(samples), max(start, end))
        return float(np.sum(np.square(samples[start:end])))

    @staticmethod
    def _window(name, start, end, energy, relative, confidence, method):
        return EnergyWindowAnalysis(
            name=name,
            start_ms=start,
            end_ms=end,
            energy=energy,
            relative_energy_db=relative,
            confidence=confidence,
            method=method,
        )

    @staticmethod
    def _relative_db(energy, total):
        if energy <= 0 or total <= 0:
            return None
        return float(10.0 * np.log10(energy / total))

    @classmethod
    def _confidence(cls, samples, energies, total):
        tail_length = max(1, len(samples) // 10)
        noise_power = float(np.mean(np.square(samples[-tail_length:])))
        mean_power = total / max(1, len(samples))
        if noise_power <= 0:
            noise_quality = 1.0
        else:
            snr_db = 10.0 * np.log10(mean_power / noise_power)
            noise_quality = min(1.0, max(0.0, snr_db) / 40.0)
        available_windows = sum(
            energy > total * cls.MINIMUM_RELATIVE_ENERGY
            for energy in (
                energies["DIRECT"],
                energies["EARLY"],
                energies["LATE"],
            )
        )
        coverage = available_windows / 3.0
        return 100.0 * (0.7 * noise_quality + 0.3 * coverage)

    @classmethod
    def _direct_index(cls, samples, impulse_response):
        global_index = int(np.argmax(np.abs(samples)))
        if impulse_response.peak_index is None:
            return global_index
        radius = max(
            1,
            round(
                cls.DIRECT_SEARCH_TOLERANCE_MS
                * impulse_response.sample_rate_hz
                / 1000.0
            ),
        )
        minimum = max(0, impulse_response.peak_index - radius)
        maximum = min(
            len(samples), impulse_response.peak_index + radius + 1
        )
        return minimum + int(np.argmax(np.abs(samples[minimum:maximum])))

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
            center > 0
            and center * cls.BAND_EDGE_FACTOR < sample_rate_hz / 2
        )

    @classmethod
    def _unavailable_band(
        cls, center, window_start, direct_end, early_end, analysis_end
    ):
        bounds = (
            ("DIRECT", window_start, direct_end),
            ("EARLY", direct_end, early_end),
            ("LATE", early_end, analysis_end),
            ("TOTAL", window_start, analysis_end),
        )
        windows = [
            cls._window(name, start, end, None, None, 0.0, cls.METHOD)
            for name, start, end in bounds
        ]
        return DirectReverberantBandAnalysis(
            center_frequency_hz=center,
            direct_window=windows[0],
            early_window=windows[1],
            late_window=windows[2],
            total_window=windows[3],
            direct_to_reverberant_db=None,
            confidence=0.0,
            method=cls.METHOD,
        )

    @staticmethod
    def _validate(response, window_start, direct_end, early_end, analysis_end):
        if response.sample_rate_hz <= 0:
            raise ValueError("Impulse response sample rate must be positive.")
        if not response.samples:
            raise ValueError("Impulse response samples are required.")
        if not window_start < direct_end < early_end:
            raise ValueError("D/R energy window bounds must be ordered.")
        if analysis_end is not None and analysis_end <= early_end:
            raise ValueError("D/R analysis end must follow the early window.")
        if (
            response.peak_index is not None
            and not 0 <= response.peak_index < len(response.samples)
        ):
            raise ValueError("Impulse response peak index is outside the samples.")
