from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

from acousticbrain.models import ETCChannelAnalysis, ImpulseResponse, ReflectionEvent
from acousticbrain.physics.room import SPEED_OF_SOUND


class ETCAnalyzer:
    """Détecte des événements temporels sans leur attribuer de cause physique."""

    DIRECT_SEARCH_TOLERANCE_MS = 1.0
    DEFAULT_ANALYSIS_WINDOW_MS = 50.0
    MINIMUM_EVENT_DELAY_MS = 0.5
    MINIMUM_EVENT_SEPARATION_MS = 0.5
    MINIMUM_RELATIVE_LEVEL_DB = -40.0
    MINIMUM_NOISE_MARGIN_DB = 10.0
    MINIMUM_PROMINENCE_DB = 3.0

    def analyze(
        self,
        impulse_response: ImpulseResponse,
        *,
        analysis_window_ms: float = DEFAULT_ANALYSIS_WINDOW_MS,
    ) -> ETCChannelAnalysis:
        self._validate(impulse_response, analysis_window_ms)
        samples = np.asarray(impulse_response.samples, dtype=float)
        direct_index = self._direct_sound_index(impulse_response, samples)
        direct_amplitude = abs(float(samples[direct_index]))
        if direct_amplitude <= 0:
            return ETCChannelAnalysis(
                channel=impulse_response.channel,
                direct_sound_time_s=None,
                direct_sound_index=None,
                analysis_window_ms=analysis_window_ms,
                confidence=0.0,
            )

        relative_level_db = self._relative_level_db(samples, direct_amplitude)
        noise_floor_db = self._noise_floor_db(samples, direct_amplitude)
        events = self._events(
            impulse_response,
            relative_level_db,
            direct_index,
            noise_floor_db,
            analysis_window_ms,
        )
        direct_time_s = self._absolute_time(impulse_response, direct_index)
        direct_confidence = self._direct_confidence(
            impulse_response,
            direct_index,
            noise_floor_db,
        )
        event_confidence = (
            float(np.mean([event.confidence for event in events]))
            if events
            else direct_confidence
        )

        return ETCChannelAnalysis(
            channel=impulse_response.channel,
            direct_sound_time_s=direct_time_s,
            direct_sound_index=direct_index,
            events=events,
            analysis_window_ms=analysis_window_ms,
            noise_floor_db=noise_floor_db,
            confidence=0.6 * direct_confidence + 0.4 * event_confidence,
        )

    @classmethod
    def _direct_sound_index(cls, impulse_response, samples):
        global_index = int(np.argmax(np.abs(samples)))
        if impulse_response.peak_index is None:
            return global_index

        radius = cls._milliseconds_to_samples(
            cls.DIRECT_SEARCH_TOLERANCE_MS,
            impulse_response.sample_rate_hz,
        )
        minimum = max(0, impulse_response.peak_index - radius)
        maximum = min(len(samples), impulse_response.peak_index + radius + 1)
        local_index = minimum + int(np.argmax(np.abs(samples[minimum:maximum])))

        if abs(samples[local_index]) >= 0.5 * abs(samples[global_index]):
            return local_index
        return global_index

    @classmethod
    def _events(
        cls,
        impulse_response,
        relative_level_db,
        direct_index,
        noise_floor_db,
        analysis_window_ms,
    ):
        sample_rate_hz = impulse_response.sample_rate_hz
        minimum_index = direct_index + cls._milliseconds_to_samples(
            cls.MINIMUM_EVENT_DELAY_MS,
            sample_rate_hz,
        )
        maximum_index = min(
            len(relative_level_db),
            direct_index
            + cls._milliseconds_to_samples(analysis_window_ms, sample_rate_hz)
            + 1,
        )
        if minimum_index >= maximum_index:
            return []

        threshold_db = max(
            cls.MINIMUM_RELATIVE_LEVEL_DB,
            (
                noise_floor_db + cls.MINIMUM_NOISE_MARGIN_DB
                if noise_floor_db is not None
                else cls.MINIMUM_RELATIVE_LEVEL_DB
            ),
        )
        window = relative_level_db[minimum_index:maximum_index]
        peaks, properties = find_peaks(
            window,
            height=threshold_db,
            prominence=cls.MINIMUM_PROMINENCE_DB,
            distance=cls._milliseconds_to_samples(
                cls.MINIMUM_EVENT_SEPARATION_MS,
                sample_rate_hz,
            ),
        )

        events = []
        for offset, level_db, prominence_db in zip(
            peaks,
            properties["peak_heights"],
            properties["prominences"],
        ):
            sample_index = minimum_index + int(offset)
            delay_seconds = (sample_index - direct_index) / sample_rate_hz
            events.append(
                ReflectionEvent(
                    delay_ms=delay_seconds * 1000.0,
                    relative_level_db=float(level_db),
                    absolute_time_s=cls._absolute_time(
                        impulse_response,
                        sample_index,
                    ),
                    sample_index=sample_index,
                    acoustic_path_difference_m=delay_seconds * SPEED_OF_SOUND,
                    confidence=cls._event_confidence(
                        float(level_db),
                        float(prominence_db),
                        noise_floor_db,
                    ),
                )
            )
        return events

    @staticmethod
    def _relative_level_db(samples, direct_amplitude):
        ratio = np.abs(samples) / direct_amplitude
        return 20.0 * np.log10(np.maximum(ratio, np.finfo(float).tiny))

    @staticmethod
    def _noise_floor_db(samples, direct_amplitude):
        tail_length = max(1, len(samples) // 10)
        noise_rms = float(np.sqrt(np.mean(np.square(samples[-tail_length:]))))
        if noise_rms <= 0:
            return None
        return float(20.0 * np.log10(noise_rms / direct_amplitude))

    @classmethod
    def _event_confidence(cls, level_db, prominence_db, noise_floor_db):
        effective_noise_floor = (
            noise_floor_db
            if noise_floor_db is not None
            else cls.MINIMUM_RELATIVE_LEVEL_DB - cls.MINIMUM_NOISE_MARGIN_DB
        )
        noise_margin = max(0.0, level_db - effective_noise_floor)
        noise_quality = min(1.0, noise_margin / 20.0)
        prominence_quality = min(1.0, prominence_db / 12.0)
        return 100.0 * (0.6 * noise_quality + 0.4 * prominence_quality)

    @classmethod
    def _direct_confidence(cls, impulse_response, direct_index, noise_floor_db):
        noise_quality = min(
            1.0,
            max(0.0, -(noise_floor_db or -60.0)) / 60.0,
        )
        if impulse_response.peak_index is None:
            location_quality = 0.8
        else:
            tolerance = cls._milliseconds_to_samples(
                cls.DIRECT_SEARCH_TOLERANCE_MS,
                impulse_response.sample_rate_hz,
            )
            distance = abs(direct_index - impulse_response.peak_index)
            location_quality = max(0.0, 1.0 - distance / max(1, tolerance))
        return 100.0 * (0.7 * noise_quality + 0.3 * location_quality)

    @staticmethod
    def _absolute_time(impulse_response, sample_index):
        start_time_s = (
            impulse_response.start_time_s
            if impulse_response.start_time_s is not None
            else impulse_response.time_offset_seconds
        )
        return start_time_s + sample_index / impulse_response.sample_rate_hz

    @staticmethod
    def _milliseconds_to_samples(milliseconds, sample_rate_hz):
        return max(1, round(milliseconds * sample_rate_hz / 1000.0))

    @staticmethod
    def _validate(impulse_response, analysis_window_ms):
        if impulse_response.sample_rate_hz <= 0:
            raise ValueError("Impulse response sample rate must be positive.")
        if not impulse_response.samples:
            raise ValueError("Impulse response samples are required.")
        if analysis_window_ms <= 0:
            raise ValueError("ETC analysis window must be positive.")
        if (
            impulse_response.peak_index is not None
            and not 0 <= impulse_response.peak_index < len(impulse_response.samples)
        ):
            raise ValueError("Impulse response peak index is outside the samples.")

