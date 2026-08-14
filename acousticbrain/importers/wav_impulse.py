import struct
import wave
from pathlib import Path

from acousticbrain.models import (
    ImpulseChannel,
    ImpulseResponse,
    PeakValueConvention,
)


class WavImpulseImporter:
    """Transforme un WAV PCM déjà affecté à un canal, sans le modifier."""

    def load(self, path, *, channel: ImpulseChannel):
        source = Path(path)
        with wave.open(str(source), "rb") as stream:
            channel_count = stream.getnchannels()
            sample_width = stream.getsampwidth()
            sample_rate = stream.getframerate()
            frame_count = stream.getnframes()
            if channel_count != 1:
                raise ValueError("REW impulse WAV exports must be mono.")
            raw = stream.readframes(frame_count)
        samples = self._samples(raw, sample_width)
        peak_index = (
            max(range(len(samples)), key=lambda index: abs(samples[index]))
            if samples
            else None
        )
        peak_value = abs(samples[peak_index]) if peak_index is not None else None
        if peak_value:
            samples = [value / peak_value for value in samples]
        return ImpulseResponse(
            channel=channel,
            sample_rate_hz=float(sample_rate),
            samples=samples,
            source_id=source.name,
            peak_value=peak_value,
            peak_index=peak_index,
            response_length=len(samples),
            sample_interval_s=1.0 / sample_rate,
            start_time_s=0.0,
            peak_value_convention=PeakValueConvention.BEFORE_NORMALIZATION,
        )

    @staticmethod
    def _samples(raw, width):
        if width == 1:
            return [(value - 128) / 128.0 for value in raw]
        if width == 2:
            values = struct.unpack(f"<{len(raw) // 2}h", raw)
            return [value / 32768.0 for value in values]
        if width == 3:
            values = []
            for index in range(0, len(raw), 3):
                value = int.from_bytes(
                    raw[index : index + 3],
                    byteorder="little",
                    signed=True,
                )
                values.append(value / 8388608.0)
            return values
        if width == 4:
            values = struct.unpack(f"<{len(raw) // 4}i", raw)
            return [value / 2147483648.0 for value in values]
        raise ValueError("Unsupported WAV sample width.")
