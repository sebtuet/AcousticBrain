from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CapturedAudio:
    emitted: np.ndarray
    recorded: np.ndarray
    diagnostics: "CaptureDiagnostics | None" = None


@dataclass(frozen=True)
class CaptureDiagnostics:
    recorded_rms_dbfs: float
    recorded_peak_dbfs: float
    clipping: bool
    captured_samples: int
    input_device: str
    output_device: str
    resolved_input_device: str
    resolved_output_device: str
    sample_rate_hz: int
    output_channel: str


class SoundDeviceCaptureEngine:
    def capture(
        self,
        sweep,
        *,
        channel,
        sample_rate_hz,
        input_device,
        output_device,
        pre_silence_s=1.0,
        post_silence_s=5.0,
    ) -> CapturedAudio:
        try:
            import sounddevice as sd
        except ImportError as error:
            raise RuntimeError(
                "Native placement capture requires the optional 'sounddevice' "
                "package. Install it before using --native-placement-capture."
            ) from error
        resolved_input = self._resolved_device(sd, input_device, "input")
        resolved_output = self._resolved_device(sd, output_device, "output")
        sweep = np.asarray(sweep, dtype=float)
        pre_silence = np.zeros(int(round(pre_silence_s * sample_rate_hz)), dtype=float)
        post_silence = np.zeros(int(round(post_silence_s * sample_rate_hz)), dtype=float)
        mono = np.concatenate((pre_silence, sweep, post_silence))
        output = np.zeros((len(mono), 2), dtype=np.float32)
        if channel == "LEFT":
            output[:, 0] = mono.astype(np.float32)
        elif channel == "RIGHT":
            output[:, 1] = mono.astype(np.float32)
        elif channel == "STEREO":
            output[:, 0] = mono.astype(np.float32)
            output[:, 1] = mono.astype(np.float32)
        else:
            raise ValueError(f"Unsupported native output channel: {channel}")
        recorded = sd.playrec(
            output,
            samplerate=sample_rate_hz,
            channels=1,
            device=(input_device, output_device),
            blocking=True,
        )
        recorded = np.asarray(recorded[:, 0], dtype=float)
        peak = float(np.max(np.abs(recorded))) if len(recorded) else 0.0
        rms = float(np.sqrt(np.mean(recorded ** 2))) if len(recorded) else 0.0
        return CapturedAudio(
            emitted=sweep,
            recorded=recorded,
            diagnostics=CaptureDiagnostics(
                recorded_rms_dbfs=self._dbfs(rms),
                recorded_peak_dbfs=self._dbfs(peak),
                clipping=peak >= 0.999,
                captured_samples=len(recorded),
                input_device=str(input_device),
                output_device=str(output_device),
                resolved_input_device=resolved_input,
                resolved_output_device=resolved_output,
                sample_rate_hz=sample_rate_hz,
                output_channel=channel,
            ),
        )

    @staticmethod
    def _dbfs(value):
        return float(20.0 * np.log10(max(value, 1e-12)))

    @staticmethod
    def _resolved_device(sd, device, kind):
        try:
            info = sd.query_devices(device, kind=kind)
        except Exception:
            return str(device)
        if isinstance(info, dict):
            name = info.get("name")
            index = info.get("index")
            if name is not None and index is not None:
                return f"{index}: {name}"
            if name is not None:
                return str(name)
        return str(device)
