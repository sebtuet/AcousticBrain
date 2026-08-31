import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import main as acousticbrain_main
from acousticbrain.acquisition import (
    NativePlacementCaptureConfig,
    NativePlacementCaptureService,
)
from acousticbrain.acquisition.calibration import load_umik_calibration
from acousticbrain.acquisition.capture import CapturedAudio, CaptureDiagnostics
from acousticbrain.acquisition.capture import SoundDeviceCaptureEngine
from acousticbrain.acquisition.response import detect_sweep, estimate_frequency_response
from acousticbrain.acquisition.sweep import SweepParameters, logarithmic_sweep
from acousticbrain.application import (
    ChannelIsolationRepeatabilityEvaluationService,
)


class FakeCaptureEngine:
    def __init__(self):
        self.calls = []

    def capture(
        self,
        sweep,
        *,
        channel,
        sample_rate_hz,
        input_device,
        output_device,
    ):
        self.calls.append((channel, sample_rate_hz, input_device, output_device))
        recorded = np.pad(sweep, (1600, 1600))
        return CapturedAudio(
            emitted=sweep,
            recorded=recorded,
            diagnostics=CaptureDiagnostics(
                recorded_rms_dbfs=-42.0,
                recorded_peak_dbfs=-18.0,
                clipping=False,
                captured_samples=len(recorded),
                input_device=input_device,
                output_device=output_device,
                resolved_input_device="1: UMIK-1",
                resolved_output_device="0: AirPlay",
                sample_rate_hz=sample_rate_hz,
                output_channel=channel,
            ),
        )


def test_native_capture_writes_rew_compatible_channel_isolation_experiment(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()
    calibration = tmp_path / "7171499_90deg.txt"
    calibration.write_text("20 0\n20000 0\n", encoding="utf-8")
    output = []
    engine = FakeCaptureEngine()
    service = NativePlacementCaptureService(
        capture_engine=engine,
        output_func=output.append,
        countdown=lambda: None,
    )

    summary = service.capture(NativePlacementCaptureConfig(
        measurements_root=root,
        input_device="UMIK-1",
        output_device="AirPlay",
        calibration_file=calibration,
        sample_rate_hz=8000,
        sweep_end_hz=3000.0,
        sweep_duration_s=0.05,
        experiment_id="exp-native-test",
    ))

    experiment = root / "exp-native-test"
    manifest = json.loads((experiment / "manifest.json").read_text(encoding="utf-8"))
    assert summary.experiment_directory == experiment
    assert [call[0] for call in engine.calls] == ["LEFT", "LEFT", "RIGHT", "RIGHT"]
    assert manifest["native_acquisition"]["experimental"] is True
    assert manifest["native_acquisition"]["identity"] == (
        "acousticbrain.native_placement_capture.v1"
    )
    assert manifest["native_acquisition"]["sample_rate_hz"] == 8000
    assert manifest["native_acquisition"]["sweep"]["duration_s"] == 0.05
    assert manifest["channel_assignments"] == {
        "measurements/LEFT exp-native-test A.txt": "LEFT",
        "measurements/LEFT exp-native-test B.txt": "LEFT",
        "measurements/RIGHT exp-native-test A.txt": "RIGHT",
        "measurements/RIGHT exp-native-test B.txt": "RIGHT",
    }
    assert (
        manifest["evidence_acquisition_plan_contract"]["plan"]["test_type"]
        == "CHANNEL_ISOLATION"
    )
    assert manifest["native_acquisition"]["captures"]["LEFT_A"][
        "recorded_rms_dbfs"
    ] == -42.0
    assert manifest["native_acquisition"]["captures"]["LEFT_A"][
        "response_window_truncated"
    ] is False
    assert manifest["native_acquisition"]["captures"]["LEFT_A"][
        "detected_sweep_start_sample"
    ] == 1600
    assert manifest["native_acquisition"]["captures"]["LEFT_A"][
        "detection_valid"
    ] is True
    assert (
        experiment / manifest["native_acquisition"]["captures"]["LEFT_A"]["raw_wav_path"]
    ).is_file()
    text = (experiment / "measurements/LEFT exp-native-test A.txt").read_text(
        encoding="utf-8"
    )
    assert "* Measurement: LEFT exp-native-test A" in text
    assert "* Freq(Hz) SPL(dB) Phase(degrees)" in text
    assert summary.evaluations
    rendered_output = "\n".join(output)
    assert "Diagnostics LEFT A :" in rendered_output
    assert "RMS -42.0 dBFS, peak -18.0 dBFS, clipping non" in rendered_output
    assert (
        "fenêtre réponse : 400/400 échantillons, disponibles 2000, tronquée non"
        in rendered_output
    )


class FakeNativeService:
    def __init__(self):
        self.configs = []

    def capture(self, config):
        self.configs.append(config)
        return SimpleNamespace(
            evaluations=(
                SimpleNamespace(
                    left_maximum_difference_db=0.34,
                    left_maximum_difference_frequency_hz=91.0,
                    right_maximum_difference_db=0.28,
                    right_maximum_difference_frequency_hz=103.0,
                    status=SimpleNamespace(value="REPEATABILITY_ACCEPTABLE_IN_BAND"),
                ),
            )
        )


def test_main_cli_runs_native_capture_as_explicit_experimental_mode(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    calibration = tmp_path / "cal.txt"
    calibration.write_text("20 0\n20000 0\n", encoding="utf-8")
    service = FakeNativeService()

    result = acousticbrain_main.main(
        [
            "--measurements-root",
            str(root),
            "--native-placement-capture",
            "--input-device",
            "UMIK-1",
            "--output-device",
            "AirPlay",
            "--calibration-file",
            str(calibration),
            "--native-experiment-id",
            "exp-native-cli",
        ],
        native_placement_capture_service=service,
    )

    assert result == 0
    assert service.configs[0].measurements_root == root
    assert service.configs[0].input_device == "UMIK-1"
    assert service.configs[0].output_device == "AirPlay"
    assert service.configs[0].calibration_file == calibration
    output = capsys.readouterr().out
    assert "Répétabilité :" in output
    assert "Gauche : 0.34 dB max à 91.0 Hz" in output
    assert "Droite : 0.28 dB max à 103.0 Hz" in output


def test_main_cli_requires_explicit_native_devices_and_calibration(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            ["--measurements-root", str(root), "--native-placement-capture"]
        )

    assert error.value.code == 2


def test_sounddevice_engine_selects_duplex_devices_with_stream_device_tuple(monkeypatch):
    calls = []

    class FakeSoundDevice:
        __version__ = "0.5.6"

        @staticmethod
        def playrec(data, **kwargs):
            assert "input_device" not in kwargs
            assert "output_device" not in kwargs
            calls.append((data, kwargs))
            return np.ones((len(data), 1), dtype=np.float32)

    monkeypatch.setitem(sys.modules, "sounddevice", FakeSoundDevice)

    captured = SoundDeviceCaptureEngine().capture(
        np.array([0.1, 0.2, 0.3], dtype=float),
        channel="RIGHT",
        sample_rate_hz=10,
        input_device="UMIK-1",
        output_device="AirPlay",
    )

    data, kwargs = calls[0]
    assert kwargs == {
        "samplerate": 10,
        "channels": 1,
        "device": ("UMIK-1", "AirPlay"),
        "blocking": True,
    }
    assert data.shape == (63, 2)
    assert np.all(data[:, 0] == 0.0)
    assert np.allclose(data[:10, 1], 0.0)
    assert np.allclose(data[10:13, 1], [0.1, 0.2, 0.3])
    assert np.allclose(data[13:, 1], 0.0)
    assert captured.recorded.tolist() == [1.0] * 63


def test_native_capture_envelope_can_contain_airplay_delayed_full_sweep(monkeypatch):
    calls = []

    class FakeSoundDevice:
        @staticmethod
        def query_devices(device, kind=None):
            return {"index": 0 if kind == "output" else 1, "name": str(device)}

        @staticmethod
        def playrec(data, **kwargs):
            calls.append((data, kwargs))
            return np.zeros((len(data), 1), dtype=np.float32)

    monkeypatch.setitem(sys.modules, "sounddevice", FakeSoundDevice)

    sample_rate_hz = 1000
    sweep = logarithmic_sweep(SweepParameters(
        sample_rate_hz=sample_rate_hz,
        start_hz=20.0,
        end_hz=400.0,
        duration_s=5.0,
        level_dbfs=-18.0,
    ))

    SoundDeviceCaptureEngine().capture(
        sweep,
        channel="LEFT",
        sample_rate_hz=sample_rate_hz,
        input_device="UMIK-1",
        output_device="AirPlay",
    )

    data, _ = calls[0]
    assert data.shape == (11000, 2)
    delay_samples = 3700
    assert len(data) - delay_samples >= len(sweep)

    rng = np.random.default_rng(789)
    recorded = np.concatenate((
        rng.normal(0.0, 0.01, delay_samples),
        sweep,
        rng.normal(0.0, 0.01, len(data) - delay_samples - len(sweep)),
    ))
    diagnostics = detect_sweep(sweep, recorded, sample_rate_hz=sample_rate_hz)

    assert diagnostics.detected_sweep_start_sample == delay_samples
    assert diagnostics.detected_sweep_start_s == 3.7
    assert diagnostics.available_samples == 7300
    assert diagnostics.response_window_truncated is False
    assert diagnostics.detection_valid is True


def test_sweep_detection_finds_delayed_sweep_after_noise():
    sample_rate_hz = 1000
    rng = np.random.default_rng(123)
    sweep = logarithmic_sweep(SweepParameters(
        sample_rate_hz=sample_rate_hz,
        start_hz=20.0,
        end_hz=400.0,
        duration_s=0.5,
        level_dbfs=-18.0,
    ))
    delay_samples = 3500
    recorded = np.concatenate((
        rng.normal(0.0, 0.01, delay_samples),
        sweep,
        rng.normal(0.0, 0.01, 700),
    ))

    diagnostics = detect_sweep(
        sweep,
        recorded,
        sample_rate_hz=sample_rate_hz,
    )

    assert diagnostics.detected_sweep_start_sample == delay_samples
    assert diagnostics.detected_sweep_start_s == 3.5
    assert diagnostics.detection_valid is True
    assert diagnostics.detection_peak_to_background_db > 12.0
    assert diagnostics.detection_peak_to_second_peak_db > 6.0
    assert diagnostics.available_samples == len(recorded) - delay_samples
    assert diagnostics.response_window_truncated is False


def test_weak_sweep_detection_is_not_silently_accepted(tmp_path):
    calibration = tmp_path / "cal.txt"
    calibration.write_text("20 0\n20000 0\n", encoding="utf-8")
    sample_rate_hz = 1000
    rng = np.random.default_rng(456)
    sweep = logarithmic_sweep(SweepParameters(
        sample_rate_hz=sample_rate_hz,
        start_hz=20.0,
        end_hz=400.0,
        duration_s=0.5,
        level_dbfs=-18.0,
    ))
    recorded = rng.normal(0.0, 0.01, 3000)

    diagnostics = detect_sweep(
        sweep,
        recorded,
        sample_rate_hz=sample_rate_hz,
    )

    assert diagnostics.detection_valid is False
    assert diagnostics.detection_peak_to_second_peak_db < 6.0
    with pytest.raises(ValueError, match="Sweep detection confidence is too low"):
        estimate_frequency_response(
            sweep,
            recorded,
            sample_rate_hz=sample_rate_hz,
            calibration=load_umik_calibration(calibration),
        )
