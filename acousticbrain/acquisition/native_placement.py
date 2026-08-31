from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from acousticbrain.application import (
    ChannelIsolationRepeatabilityEvaluationService,
)
from acousticbrain.application.experiment_discovery import ExperimentDiscoveryService
from acousticbrain.models import ImpulseChannel
from acousticbrain.persistence import MeasurementRepository

from .calibration import load_umik_calibration
from .capture import SoundDeviceCaptureEngine
from .response import detect_sweep, estimate_frequency_response
from .sweep import SweepParameters, logarithmic_sweep


@dataclass(frozen=True)
class NativePlacementCaptureConfig:
    measurements_root: Path
    input_device: str
    output_device: str
    calibration_file: Path
    sample_rate_hz: int = 44100
    sweep_start_hz: float = 20.0
    sweep_end_hz: float = 20000.0
    sweep_duration_s: float = 5.0
    sweep_level_dbfs: float = -24.0
    experiment_id: str | None = None


@dataclass(frozen=True)
class NativePlacementCaptureSummary:
    experiment_id: str
    experiment_directory: Path
    evaluations: tuple


class NativePlacementCaptureService:
    SEQUENCE = (
        (ImpulseChannel.LEFT, "A"),
        (ImpulseChannel.LEFT, "B"),
        (ImpulseChannel.RIGHT, "A"),
        (ImpulseChannel.RIGHT, "B"),
    )

    def __init__(
        self,
        *,
        capture_engine=None,
        discovery_service=None,
        repeatability_evaluation_service=None,
        clock=None,
        countdown=None,
        output_func=print,
    ):
        self.capture_engine = capture_engine or SoundDeviceCaptureEngine()
        self.discovery_service = discovery_service or ExperimentDiscoveryService()
        self.repeatability_evaluation_service = (
            repeatability_evaluation_service
            or ChannelIsolationRepeatabilityEvaluationService()
        )
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.countdown = countdown or self._countdown
        self.output_func = output_func

    def capture(self, config: NativePlacementCaptureConfig) -> NativePlacementCaptureSummary:
        parameters = SweepParameters(
            sample_rate_hz=config.sample_rate_hz,
            start_hz=config.sweep_start_hz,
            end_hz=config.sweep_end_hz,
            duration_s=config.sweep_duration_s,
            level_dbfs=config.sweep_level_dbfs,
        )
        calibration = load_umik_calibration(config.calibration_file)
        experiment_id = config.experiment_id or self._experiment_id()
        experiment_directory = Path(config.measurements_root) / experiment_id
        measurements_directory = experiment_directory / "measurements"
        diagnostics_directory = experiment_directory / "native-diagnostics"
        measurements_directory.mkdir(parents=True, exist_ok=False)
        diagnostics_directory.mkdir(parents=True, exist_ok=True)
        emitted = logarithmic_sweep(parameters)

        self._print_header(config)
        written = {}
        capture_diagnostics = {}
        for channel, repeat in self.SEQUENCE:
            label = f"{channel.value} {repeat}"
            self.output_func(f"{label} dans 3...")
            self.countdown()
            self.output_func("[sweep]")
            captured = self.capture_engine.capture(
                emitted,
                channel=channel.value,
                sample_rate_hz=parameters.sample_rate_hz,
                input_device=config.input_device,
                output_device=config.output_device,
            )
            raw_wav_relative_path = f"native-diagnostics/{channel.value}_{repeat}.wav"
            self._write_raw_wav(
                experiment_directory / raw_wav_relative_path,
                sample_rate_hz=parameters.sample_rate_hz,
                recorded=captured.recorded,
            )
            detection = detect_sweep(
                captured.emitted,
                captured.recorded,
                sample_rate_hz=parameters.sample_rate_hz,
            )
            response = None
            if detection.detection_valid:
                response = estimate_frequency_response(
                    captured.emitted,
                    captured.recorded,
                    sample_rate_hz=parameters.sample_rate_hz,
                    calibration=calibration,
                )
            self._print_capture_diagnostics(
                label,
                captured,
                response.diagnostics if response is not None else detection,
            )
            if response is not None:
                relative_path = f"measurements/{channel.value} {experiment_id} {repeat}.txt"
                self._write_rew_compatible_txt(
                    experiment_directory / relative_path,
                    measurement_name=f"{channel.value} {experiment_id} {repeat}",
                    response=response,
                )
                written[relative_path] = channel.value
            capture_diagnostics[label.replace(" ", "_")] = (
                self._capture_diagnostics_dict(
                    captured,
                    response.diagnostics if response is not None else detection,
                    raw_wav_relative_path,
                )
            )

        MeasurementRepository.save_manifest(
            experiment_directory,
            self._manifest(
                config,
                parameters,
                calibration.path,
                written,
                capture_diagnostics,
            ),
        )
        descriptors = self.discovery_service.discover(config.measurements_root)
        evaluations = self.repeatability_evaluation_service.evaluate(
            tuple(item for item in descriptors if item.experiment_id == experiment_id)
        )
        self.output_func("Acquisition terminée.")
        return NativePlacementCaptureSummary(
            experiment_id=experiment_id,
            experiment_directory=experiment_directory,
            evaluations=evaluations,
        )

    def _print_header(self, config):
        self.output_func("Acquisition native expérimentale")
        self.output_func("")
        self.output_func(f"Microphone : {config.input_device}")
        self.output_func(f"Sortie : {config.output_device}")
        self.output_func(f"Calibration : {Path(config.calibration_file).name}")
        self.output_func(f"Sample rate : {config.sample_rate_hz} Hz")
        self.output_func("Séquence : LEFT A, LEFT B, RIGHT A, RIGHT B")
        self.output_func("")

    def _print_capture_diagnostics(self, label, captured, response_diagnostics):
        capture = captured.diagnostics
        if capture is None or response_diagnostics is None:
            return
        self.output_func(f"Diagnostics {label} :")
        self.output_func(
            "  signal enregistré : "
            f"RMS {capture.recorded_rms_dbfs:.1f} dBFS, "
            f"peak {capture.recorded_peak_dbfs:.1f} dBFS, "
            f"clipping {'oui' if capture.clipping else 'non'}"
        )
        self.output_func(
            "  sweep détecté : "
            f"sample {response_diagnostics.detected_sweep_start_sample} "
            f"({response_diagnostics.detected_sweep_start_s:.3f} s), "
            f"corrélation norm. "
            f"{response_diagnostics.detection_normalized_correlation:.3f}, "
            f"valide {'oui' if response_diagnostics.detection_valid else 'non'}"
        )
        self.output_func(
            "  corrélation brute : "
            f"pic {response_diagnostics.detection_peak_value:.6g}, "
            f"fond {response_diagnostics.detection_background_value:.6g}, "
            f"second pic "
            f"{self._format_optional_float(response_diagnostics.detection_second_peak_value)}, "
            f"pic/fond {response_diagnostics.detection_peak_to_background_db:.1f} dB, "
            f"pic/second {response_diagnostics.detection_peak_to_second_peak_db:.1f} dB"
        )
        self.output_func(
            "  capture : "
            f"{capture.captured_samples} échantillons, "
            f"sample rate {capture.sample_rate_hz} Hz, "
            f"sortie {capture.output_channel}"
        )
        self.output_func(
            "  devices : "
            f"input {capture.resolved_input_device}, "
            f"output {capture.resolved_output_device}"
        )
        self.output_func(
            "  fenêtre réponse : "
            f"{response_diagnostics.response_window_samples}/"
            f"{response_diagnostics.sweep_samples} échantillons, "
            f"disponibles {response_diagnostics.available_samples}, "
            f"tronquée {'oui' if response_diagnostics.response_window_truncated else 'non'}"
        )
        low_min = response_diagnostics.response_30_200_min_db
        low_max = response_diagnostics.response_30_200_max_db
        low_stats = (
            "n/a"
            if low_min is None or low_max is None
            else f"{low_min:.1f}..{low_max:.1f} dB"
        )
        self.output_func(
            "  réponse avant TXT : "
            f"{response_diagnostics.response_points} points, "
            f"min/max {response_diagnostics.response_min_db:.1f}/"
            f"{response_diagnostics.response_max_db:.1f} dB, "
            f"moyenne {response_diagnostics.response_mean_db:.1f} dB, "
            f"30-200 Hz {low_stats}"
        )

    def _capture_diagnostics_dict(self, captured, response_diagnostics, raw_wav_path):
        capture = captured.diagnostics
        if capture is None or response_diagnostics is None:
            return {}
        return {
            "raw_wav_path": raw_wav_path,
            "recorded_rms_dbfs": capture.recorded_rms_dbfs,
            "recorded_peak_dbfs": capture.recorded_peak_dbfs,
            "clipping": capture.clipping,
            "captured_samples": capture.captured_samples,
            "input_device": capture.input_device,
            "output_device": capture.output_device,
            "resolved_input_device": capture.resolved_input_device,
            "resolved_output_device": capture.resolved_output_device,
            "sample_rate_hz": capture.sample_rate_hz,
            "output_channel": capture.output_channel,
            "detected_sweep_start_sample": (
                response_diagnostics.detected_sweep_start_sample
            ),
            "detected_sweep_start_s": response_diagnostics.detected_sweep_start_s,
            "detection_normalized_correlation": (
                response_diagnostics.detection_normalized_correlation
            ),
            "detection_peak_value": response_diagnostics.detection_peak_value,
            "detection_background_value": (
                response_diagnostics.detection_background_value
            ),
            "detection_second_peak_value": (
                response_diagnostics.detection_second_peak_value
            ),
            "detection_peak_to_background_db": (
                response_diagnostics.detection_peak_to_background_db
            ),
            "detection_peak_to_second_peak_db": (
                response_diagnostics.detection_peak_to_second_peak_db
            ),
            "detection_valid": response_diagnostics.detection_valid,
            "sweep_samples": response_diagnostics.sweep_samples,
            "available_samples": response_diagnostics.available_samples,
            "response_window_samples": response_diagnostics.response_window_samples,
            "response_window_truncated": (
                response_diagnostics.response_window_truncated
            ),
            "response_points": response_diagnostics.response_points,
            "response_min_db": response_diagnostics.response_min_db,
            "response_max_db": response_diagnostics.response_max_db,
            "response_mean_db": response_diagnostics.response_mean_db,
            "response_30_200_min_db": response_diagnostics.response_30_200_min_db,
            "response_30_200_max_db": response_diagnostics.response_30_200_max_db,
        }

    def _write_raw_wav(self, path, *, sample_rate_hz, recorded):
        clipped = np.clip(np.asarray(recorded, dtype=float), -1.0, 1.0)
        samples = np.round(clipped * 32767.0).astype("<i2")
        wavfile.write(path, sample_rate_hz, samples)

    @staticmethod
    def _format_optional_float(value):
        return "n/a" if value is None else f"{value:.6g}"

    def _manifest(
        self,
        config,
        parameters,
        calibration_path,
        channel_assignments,
        capture_diagnostics,
    ):
        plan_id = "native-placement-capture.channel-isolation.v1"
        return {
            "source_evidence_acquisition_plan_id": plan_id,
            "channel_assignments": channel_assignments,
            "native_acquisition": {
                "schema_version": 1,
                "identity": "acousticbrain.native_placement_capture.v1",
                "experimental": True,
                "input_device": str(config.input_device),
                "output_device": str(config.output_device),
                "calibration_file": str(Path(calibration_path).resolve()),
                "sample_rate_hz": parameters.sample_rate_hz,
                "sweep": {
                    "type": "logarithmic",
                    "start_hz": parameters.start_hz,
                    "end_hz": parameters.end_hz,
                    "duration_s": parameters.duration_s,
                    "level_dbfs": parameters.level_dbfs,
                },
                "sequence": [
                    {"channel": channel.value, "repeat": repeat}
                    for channel, repeat in self.SEQUENCE
                ],
                "captures": capture_diagnostics,
            },
            "evidence_acquisition_plan_contract": {
                "schema_version": 1,
                "mode": "EXPLORATORY",
                "declaration_source": "native-placement-capture",
                "reference_experiment_code": "baseline",
                "declaration_user_note": (
                    "Experimental native acquisition source; REW import path remains supported."
                ),
                "plan": {
                    "plan_id": plan_id,
                    "reasoning_id": "native-placement-capture",
                    "corrective_action_id": "native-placement-capture",
                    "evidence_weight_id": "native-placement-capture",
                    "blocking_factor_ids": ["NATIVE_CAPTURE_EXPERIMENTAL"],
                    "objective": "Capture LEFT/RIGHT A/B repeatability natively.",
                    "test_type": "CHANNEL_ISOLATION",
                    "instructions": ["Capture LEFT A, LEFT B, RIGHT A, RIGHT B."],
                    "required_inputs": ["UMIK_CALIBRATION", "STEREO_OUTPUT"],
                    "controlled_variables": ["MICROPHONE_POSITION", "LOUDSPEAKER_POSITION"],
                    "independent_variables": ["REPEAT_LABEL"],
                    "measurements_to_capture": ["LEFT_A", "LEFT_B", "RIGHT_A", "RIGHT_B"],
                    "expected_observations": ["A_B_REPEATABILITY"],
                    "success_criteria": ["TXT_MEASUREMENTS_DISCOVERABLE"],
                    "failure_criteria": ["CAPTURE_NOT_COMPLETED"],
                    "resulting_evidence_targets": ["CHANNEL_ISOLATION_REPEATABILITY"],
                    "priority": "MEDIUM",
                    "estimated_effort": "LOW",
                    "status": "READY",
                    "limitations": ["Experimental native acquisition; no contractual threshold changes."],
                    "channel_isolation_evaluation_criteria": [],
                },
            },
            "channel_isolation_declaration": {
                "repeated_channels": ["LEFT", "RIGHT"],
                "available_inputs": ["UMIK_CALIBRATION", "STEREO_OUTPUT"],
                "controlled_variables": ["MICROPHONE_POSITION", "LOUDSPEAKER_POSITION"],
                "independent_variables": ["REPEAT_LABEL"],
                "measurements": ["LEFT_A", "LEFT_B", "RIGHT_A", "RIGHT_B"],
            },
        }

    def _write_rew_compatible_txt(self, path, *, measurement_name, response):
        with Path(path).open("w", encoding="utf-8") as stream:
            stream.write(f"* Measurement: {measurement_name}\n")
            stream.write("* Freq(Hz) SPL(dB) Phase(degrees)\n")
            for frequency, spl, phase in zip(
                response.frequency_hz,
                response.spl_db,
                response.phase_deg,
            ):
                stream.write(f"{frequency:.6f}\t{spl:.6f}\t{phase:.6f}\n")

    def _experiment_id(self):
        return "exp-native-" + self.clock().strftime("%Y%m%d-%H%M%S")

    def _countdown(self):
        self.output_func("2...")
        self.output_func("1...")
