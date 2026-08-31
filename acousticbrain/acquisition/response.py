from dataclasses import dataclass

import numpy as np
from scipy import signal

from .calibration import MicrophoneCalibration


@dataclass(frozen=True)
class FrequencyResponse:
    frequency_hz: np.ndarray
    spl_db: np.ndarray
    phase_deg: np.ndarray
    diagnostics: "ResponseDiagnostics | None" = None


@dataclass(frozen=True)
class ResponseDiagnostics:
    detected_sweep_start_sample: int
    detected_sweep_start_s: float
    detection_normalized_correlation: float
    detection_peak_value: float
    detection_background_value: float
    detection_second_peak_value: float | None
    detection_peak_to_background_db: float
    detection_peak_to_second_peak_db: float
    detection_valid: bool
    recorded_samples: int
    sweep_samples: int
    available_samples: int
    response_window_samples: int
    response_window_truncated: bool
    response_points: int
    response_min_db: float
    response_max_db: float
    response_mean_db: float
    response_30_200_min_db: float | None
    response_30_200_max_db: float | None


def estimate_frequency_response(
    sweep,
    recorded,
    *,
    sample_rate_hz,
    calibration: MicrophoneCalibration,
    points=384,
) -> FrequencyResponse:
    sweep = np.asarray(sweep, dtype=float)
    recorded = np.asarray(recorded, dtype=float)
    if len(sweep) == 0 or len(recorded) < len(sweep):
        raise ValueError("Recorded sweep is shorter than the emitted sweep.")
    detection = detect_sweep(sweep, recorded, sample_rate_hz=sample_rate_hz)
    if not detection.detection_valid:
        raise ValueError(
            "Sweep detection confidence is too low: "
            f"{detection.detection_peak_to_background_db:.1f} dB "
            "peak/background contrast."
        )
    start = detection.detected_sweep_start_sample
    captured = recorded[start:start + len(sweep)]
    response_window_samples = len(captured)
    response_window_truncated = response_window_samples < len(sweep)
    if len(captured) < len(sweep):
        captured = np.pad(captured, (0, len(sweep) - len(captured)))
    frequencies, transfer = signal.csd(
        captured,
        sweep,
        fs=sample_rate_hz,
        nperseg=min(8192, len(sweep)),
    )
    _, reference = signal.welch(
        sweep,
        fs=sample_rate_hz,
        nperseg=min(8192, len(sweep)),
    )
    valid = (frequencies >= 20.0) & (frequencies <= 20000.0) & (reference > 0)
    frequencies = frequencies[valid]
    response = transfer[valid] / reference[valid]
    target = np.geomspace(20.0, 20000.0, points)
    magnitude_db = 20.0 * np.log10(np.maximum(np.abs(response), 1e-12))
    magnitude_db = np.interp(target, frequencies, magnitude_db)
    magnitude_db += calibration.correction_for(target)
    phase = np.unwrap(np.angle(response))
    phase_deg = np.degrees(np.interp(target, frequencies, phase))
    low_band = (target >= 30.0) & (target <= 200.0)
    return FrequencyResponse(
        target,
        magnitude_db,
        phase_deg,
        diagnostics=ResponseDiagnostics(
            detected_sweep_start_sample=start,
            detected_sweep_start_s=start / sample_rate_hz,
            detection_normalized_correlation=(
                detection.detection_normalized_correlation
            ),
            detection_peak_value=detection.detection_peak_value,
            detection_background_value=detection.detection_background_value,
            detection_second_peak_value=detection.detection_second_peak_value,
            detection_peak_to_background_db=(
                detection.detection_peak_to_background_db
            ),
            detection_peak_to_second_peak_db=(
                detection.detection_peak_to_second_peak_db
            ),
            detection_valid=detection.detection_valid,
            recorded_samples=len(recorded),
            sweep_samples=len(sweep),
            available_samples=len(recorded) - start,
            response_window_samples=response_window_samples,
            response_window_truncated=response_window_truncated,
            response_points=len(target),
            response_min_db=float(np.min(magnitude_db)),
            response_max_db=float(np.max(magnitude_db)),
            response_mean_db=float(np.mean(magnitude_db)),
            response_30_200_min_db=(
                float(np.min(magnitude_db[low_band])) if np.any(low_band) else None
            ),
            response_30_200_max_db=(
                float(np.max(magnitude_db[low_band])) if np.any(low_band) else None
            ),
        ),
    )


def _detected_sweep_start(sweep, recorded):
    return detect_sweep(sweep, recorded).detected_sweep_start_sample


def detect_sweep(
    sweep,
    recorded,
    *,
    sample_rate_hz=1,
    minimum_peak_to_background_db=12.0,
    minimum_peak_to_second_peak_db=6.0,
    minimum_normalized_correlation=0.05,
) -> ResponseDiagnostics:
    sweep = np.asarray(sweep, dtype=float)
    recorded = np.asarray(recorded, dtype=float)
    correlation = np.abs(signal.correlate(recorded, sweep, mode="valid", method="fft"))
    if len(correlation) == 0:
        return _empty_detection(len(recorded), len(sweep))
    start = int(np.argmax(np.abs(correlation)))
    sweep_energy = float(np.sum(sweep ** 2))
    window_energy = signal.convolve(
        recorded ** 2,
        np.ones(len(sweep), dtype=float),
        mode="valid",
        method="fft",
    )
    denominator = np.sqrt(np.maximum(window_energy[start] * sweep_energy, 1e-24))
    normalized = float(correlation[start] / denominator)
    peak = float(correlation[start])
    background = _correlation_background(correlation, start, len(sweep))
    second_peak = _correlation_second_peak(correlation, start, len(sweep))
    contrast = _ratio_db(peak, background)
    second_peak_contrast = (
        _ratio_db(peak, second_peak) if second_peak is not None else 0.0
    )
    return ResponseDiagnostics(
        detected_sweep_start_sample=start,
        detected_sweep_start_s=start / sample_rate_hz,
        detection_normalized_correlation=normalized,
        detection_peak_value=peak,
        detection_background_value=background,
        detection_second_peak_value=second_peak,
        detection_peak_to_background_db=contrast,
        detection_peak_to_second_peak_db=second_peak_contrast,
        detection_valid=(
            contrast >= minimum_peak_to_background_db
            and second_peak_contrast >= minimum_peak_to_second_peak_db
            and normalized >= minimum_normalized_correlation
        ),
        recorded_samples=len(recorded),
        sweep_samples=len(sweep),
        available_samples=len(recorded) - start,
        response_window_samples=0,
        response_window_truncated=(len(recorded) - start) < len(sweep),
        response_points=0,
        response_min_db=0.0,
        response_max_db=0.0,
        response_mean_db=0.0,
        response_30_200_min_db=None,
        response_30_200_max_db=None,
    )


def _empty_detection(recorded_samples, sweep_samples):
    return ResponseDiagnostics(
        detected_sweep_start_sample=0,
        detected_sweep_start_s=0.0,
        detection_normalized_correlation=0.0,
        detection_peak_value=0.0,
        detection_background_value=0.0,
        detection_second_peak_value=0.0,
        detection_peak_to_background_db=0.0,
        detection_peak_to_second_peak_db=0.0,
        detection_valid=False,
        recorded_samples=recorded_samples,
        sweep_samples=sweep_samples,
        available_samples=recorded_samples,
        response_window_samples=0,
        response_window_truncated=recorded_samples < sweep_samples,
        response_points=0,
        response_min_db=0.0,
        response_max_db=0.0,
        response_mean_db=0.0,
        response_30_200_min_db=None,
        response_30_200_max_db=None,
    )


def _correlation_background(correlation, peak_index, sweep_samples):
    guard = max(1, sweep_samples // 4)
    mask = np.ones(len(correlation), dtype=bool)
    lower = max(0, peak_index - guard)
    upper = min(len(correlation), peak_index + guard + 1)
    mask[lower:upper] = False
    background = correlation[mask]
    if len(background) == 0:
        background = correlation
    return float(np.median(np.maximum(background, 1e-24)))


def _correlation_second_peak(correlation, peak_index, sweep_samples):
    guard = max(1, sweep_samples // 4)
    mask = np.ones(len(correlation), dtype=bool)
    lower = max(0, peak_index - guard)
    upper = min(len(correlation), peak_index + guard + 1)
    mask[lower:upper] = False
    candidates = correlation[mask]
    if len(candidates) == 0:
        return None
    return float(np.max(candidates))


def _ratio_db(numerator, denominator):
    return float(20.0 * np.log10(max(numerator, 1e-24) / max(denominator, 1e-24)))
