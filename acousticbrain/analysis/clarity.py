from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfiltfilt

from acousticbrain.models import (
    ClarityBandAnalysis,
    ClarityChannelAnalysis,
    ImpulseResponse,
)


class ClarityAnalyzer:
    """Calcule les indicateurs temporels mono-canal par tiers d'octave."""

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
    METHOD = "THIRD_OCTAVE_ENERGY_INTEGRATION"
    EARLY_50_MS = 0.050
    EARLY_80_MS = 0.080
    MINIMUM_ENERGY_RATIO = 1e-12
    NOISE_MARGIN_DB = 10.0

    def analyze(
        self,
        impulse_response: ImpulseResponse,
        *,
        center_frequencies_hz: tuple[float, ...] | None = None,
    ) -> ClarityChannelAnalysis:
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

        return ClarityChannelAnalysis(
            channel=impulse_response.channel,
            band_analyses=bands,
            broadband_c50_db=self._median(bands, "c50_db"),
            broadband_c80_db=self._median(bands, "c80_db"),
            broadband_d50_percent=self._median(bands, "d50_percent"),
            broadband_ts_s=self._median(bands, "ts_s"),
            confidence=(
                float(np.mean([band.confidence for band in bands]))
                if bands
                else 0.0
            ),
        )

    def _analyze_band(self, impulse_response, center_frequency_hz):
        unavailable = self._unavailable_band(center_frequency_hz)
        minimum_hz = center_frequency_hz / self.BAND_EDGE_FACTOR
        maximum_hz = center_frequency_hz * self.BAND_EDGE_FACTOR
        try:
            filtered = self._filter(
                impulse_response.samples,
                impulse_response.sample_rate_hz,
                minimum_hz,
                maximum_hz,
            )
        except ValueError:
            return unavailable

        direct_index = self._direct_sound_index(impulse_response)
        decay = filtered[direct_index:]
        if len(decay) < 2:
            return unavailable

        energy = np.square(decay)
        total_energy = float(np.sum(energy))
        if not np.isfinite(total_energy) or total_energy <= 0:
            return unavailable

        sample_rate_hz = impulse_response.sample_rate_hz
        split_50 = min(len(energy), round(self.EARLY_50_MS * sample_rate_hz))
        split_80 = min(len(energy), round(self.EARLY_80_MS * sample_rate_hz))
        early_50 = float(np.sum(energy[:split_50]))
        early_80 = float(np.sum(energy[:split_80]))
        late_50 = float(np.sum(energy[split_50:]))
        late_80 = float(np.sum(energy[split_80:]))
        minimum_energy = total_energy * self.MINIMUM_ENERGY_RATIO

        c50_db = self._clarity_db(early_50, late_50, minimum_energy)
        c80_db = self._clarity_db(early_80, late_80, minimum_energy)
        d50_percent = (
            100.0 * early_50 / total_energy
            if early_50 > minimum_energy
            else None
        )
        times = np.arange(len(energy), dtype=float) / sample_rate_hz
        ts_s = float(np.sum(times * energy) / total_energy)
        confidence = self._confidence(
            energy,
            total_energy,
            late_50,
            late_80,
        )

        return ClarityBandAnalysis(
            center_frequency_hz=center_frequency_hz,
            c50_db=c50_db,
            c80_db=c80_db,
            d50_percent=d50_percent,
            ts_s=ts_s,
            confidence=confidence,
            method=self.METHOD,
        )

    @classmethod
    def _confidence(cls, energy, total_energy, late_50, late_80):
        tail_length = max(1, len(energy) // 10)
        noise_power = float(np.mean(energy[-tail_length:]))
        mean_power = total_energy / len(energy)
        if noise_power <= 0:
            noise_quality = 1.0
        else:
            signal_to_noise_db = 10.0 * np.log10(mean_power / noise_power)
            noise_quality = min(
                1.0,
                max(0.0, signal_to_noise_db - cls.NOISE_MARGIN_DB) / 30.0,
            )
        late_quality = 0.5 * (
            float(late_50 > total_energy * cls.MINIMUM_ENERGY_RATIO)
            + float(late_80 > total_energy * cls.MINIMUM_ENERGY_RATIO)
        )
        return 100.0 * (0.8 * noise_quality + 0.2 * late_quality)

    @staticmethod
    def _clarity_db(early_energy, late_energy, minimum_energy):
        if early_energy <= minimum_energy or late_energy <= minimum_energy:
            return None
        return float(10.0 * np.log10(early_energy / late_energy))

    @staticmethod
    def _direct_sound_index(impulse_response):
        if impulse_response.peak_index is not None:
            return impulse_response.peak_index
        return int(np.argmax(np.abs(impulse_response.samples)))

    @staticmethod
    def _median(bands, attribute):
        values = [
            value
            for band in bands
            if (value := getattr(band, attribute)) is not None
        ]
        return float(np.median(values)) if values else None

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
    def _unavailable_band(center_frequency_hz):
        return ClarityBandAnalysis(
            center_frequency_hz=center_frequency_hz,
            c50_db=None,
            c80_db=None,
            d50_percent=None,
            ts_s=None,
            confidence=0.0,
            method=None,
        )

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
