import hashlib
import json
import re
import struct
import unicodedata
import wave
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from acousticbrain.models import (
    ExperimentFileType,
    ImpulseChannel,
)


@dataclass(frozen=True)
class InspectedMeasurementFile:
    path: Path
    file_type: ExperimentFileType
    sha256: str
    channel: ImpulseChannel | None
    timestamp: str | None = None


class MeasurementRepository:
    """Accès disque, détection de format et validation, sans décision métier."""

    SUPPORTED_SUFFIXES = {".wav", ".txt", ".mdat"}

    def list_directories(self, root) -> tuple[Path, ...]:
        path = Path(root)
        if not path.is_dir():
            raise NotADirectoryError(path)
        return tuple(sorted((item for item in path.iterdir() if item.is_dir())))

    def inspect_directory(
        self,
        directory,
        *,
        channel_assignments=None,
    ) -> tuple[InspectedMeasurementFile, ...]:
        directory = Path(directory)
        assignments = channel_assignments or {}
        inspected = []
        for path in sorted(
            item
            for item in directory.rglob("*")
            if item.is_file()
            and item.name != "manifest.json"
            and item.suffix.lower() in self.SUPPORTED_SUFFIXES
        ):
            relative = path.relative_to(directory).as_posix()
            suffix = path.suffix.lower()
            if suffix == ".txt":
                file_type, detected_channel, timestamp = self.inspect_text(path)
            elif suffix == ".wav":
                detected_channel = self.inspect_wav(path)
                file_type = ExperimentFileType.WAV
                timestamp = None
            else:
                file_type = ExperimentFileType.MDAT
                detected_channel = None
                timestamp = None
            assigned = assignments.get(relative)
            channel = (
                ImpulseChannel(assigned)
                if assigned in {item.value for item in ImpulseChannel}
                else detected_channel
            )
            inspected.append(
                InspectedMeasurementFile(
                    path=path,
                    file_type=file_type,
                    sha256=self.hash_file(path),
                    channel=channel,
                    timestamp=timestamp,
                )
            )
        return tuple(inspected)

    def associate_wav_channels(self, files):
        """Associe des exports WAV/TXT par empreinte spectrale non ambiguë."""

        wav_files = [
            item
            for item in files
            if item.file_type is ExperimentFileType.WAV and item.channel is None
        ]
        measurements = [
            item
            for item in files
            if item.file_type is ExperimentFileType.TXT_MEASUREMENT
            and item.channel is not None
        ]
        if not wav_files or not measurements:
            return tuple(files)
        scores = {
            (wav.path, measurement.path): self._spectral_similarity(
                wav.path, measurement.path
            )
            for wav in wav_files
            for measurement in measurements
        }
        candidates = sorted(
            (
                (score, wav.path, measurement)
                for (wav_path, measurement_path), score in scores.items()
                for wav in wav_files
                if wav.path == wav_path
                for measurement in measurements
                if measurement.path == measurement_path
            ),
            key=lambda item: (-item[0], str(item[1]), str(item[2].path)),
        )
        assigned_wavs = set()
        assigned_measurements = set()
        channels = {}
        for score, wav_path, measurement in candidates:
            if score < 0.75:
                continue
            row = sorted(
                (
                    value
                    for (candidate_wav, _), value in scores.items()
                    if candidate_wav == wav_path
                ),
                reverse=True,
            )
            if len(row) > 1 and row[0] - row[1] < 0.03:
                continue
            if score != row[0]:
                continue
            column = sorted(
                (
                    value
                    for (_, candidate_measurement), value in scores.items()
                    if candidate_measurement == measurement.path
                ),
                reverse=True,
            )
            if len(column) > 1 and column[0] - column[1] < 0.03:
                continue
            if score != column[0]:
                continue
            if wav_path in assigned_wavs or measurement.path in assigned_measurements:
                continue
            channels[wav_path] = measurement.channel
            assigned_wavs.add(wav_path)
            assigned_measurements.add(measurement.path)
        return tuple(
            replace(item, channel=channels[item.path])
            if item.path in channels
            else item
            for item in files
        )

    def inspect_text(self, path):
        measurement_name = None
        timestamp = None
        file_type = ExperimentFileType.TXT_UNKNOWN
        with Path(path).open("r", encoding="utf-8", errors="ignore") as stream:
            for raw_line in stream:
                line = raw_line.strip()
                if line.startswith("* Measurement:"):
                    measurement_name = line.removeprefix("* Measurement:").strip()
                elif line.startswith("* Dated:"):
                    timestamp = self._rew_timestamp(
                        line.removeprefix("* Dated:").strip()
                    )
                elif line == "* Data start":
                    file_type = ExperimentFileType.TXT_IMPULSE
                    break
                elif line.startswith(("* Freq(Hz)", "Freq(Hz)")):
                    file_type = ExperimentFileType.TXT_MEASUREMENT
                    break
        return file_type, self.detect_channel(measurement_name), timestamp

    def inspect_wav(self, path):
        with wave.open(str(path), "rb") as stream:
            if stream.getnchannels() < 1 or stream.getframerate() < 1:
                raise ValueError(f"Invalid WAV export: {path}")
        metadata = self._wav_metadata(path)
        return self.detect_channel(" ".join(metadata))

    @staticmethod
    def detect_channel(value):
        if not value:
            return None
        normalized = unicodedata.normalize("NFKD", value)
        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        ).upper()
        if re.search(r"(?:^|\W)(?:L\s*\+\s*R|R\s*\+\s*L|STEREO)(?:$|\W)", normalized):
            return ImpulseChannel.STEREO
        tokens = set(re.findall(r"[A-Z]+", normalized))
        left = bool(tokens.intersection({"L", "LEFT", "GAUCHE"}))
        right = bool(tokens.intersection({"R", "RIGHT", "DROITE"}))
        if left and right:
            return ImpulseChannel.STEREO
        if left:
            return ImpulseChannel.LEFT
        if right:
            return ImpulseChannel.RIGHT
        if tokens.intersection({"SUB", "SUBWOOFER"}):
            return ImpulseChannel.SUB
        return None

    @staticmethod
    def hash_file(path):
        digest = hashlib.sha256()
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def aggregate_hash(files):
        digest = hashlib.sha256()
        for file_hash in sorted(item.sha256 for item in files):
            digest.update(file_hash.encode("ascii"))
        return digest.hexdigest()

    @staticmethod
    def load_manifest(directory):
        path = Path(directory) / "manifest.json"
        if not path.is_file():
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeError):
            return None
        return value if isinstance(value, dict) else None

    @staticmethod
    def save_manifest(directory, payload):
        path = Path(directory) / "manifest.json"
        serialized = json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        ) + "\n"
        if path.is_file() and path.read_text(encoding="utf-8") == serialized:
            return False
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(path)
        return True

    @staticmethod
    def file_timestamp(path):
        timestamp = Path(path).stat().st_mtime
        return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()

    @staticmethod
    def _rew_timestamp(value):
        match = re.fullmatch(
            r"([A-Za-z]{3}) (\d{1,2}), (\d{4}) "
            r"(\d{1,2}):(\d{2}):(\d{2}) (AM|PM)",
            value,
        )
        months = {
            "JAN": 1,
            "FEB": 2,
            "MAR": 3,
            "APR": 4,
            "MAY": 5,
            "JUN": 6,
            "JUL": 7,
            "AUG": 8,
            "SEP": 9,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
        }
        if match is None or match.group(1).upper() not in months:
            return None
        hour = int(match.group(4)) % 12
        if match.group(7) == "PM":
            hour += 12
        parsed = datetime(
            int(match.group(3)),
            months[match.group(1).upper()],
            int(match.group(2)),
            hour,
            int(match.group(5)),
            int(match.group(6)),
        )
        return parsed.isoformat()

    @staticmethod
    def _wav_metadata(path):
        values = []
        with Path(path).open("rb") as stream:
            if stream.read(4) != b"RIFF":
                return ()
            stream.seek(8)
            if stream.read(4) != b"WAVE":
                return ()
            while True:
                header = stream.read(8)
                if len(header) != 8:
                    break
                chunk_id, size = struct.unpack("<4sI", header)
                if chunk_id == b"data":
                    stream.seek(size + size % 2, 1)
                    continue
                data = stream.read(size)
                if size % 2:
                    stream.read(1)
                if chunk_id == b"bext":
                    values.append(data[:256].decode("utf-8", errors="ignore"))
                elif chunk_id == b"LIST":
                    values.extend(
                        item.decode("utf-8", errors="ignore")
                        for item in re.findall(rb"[\x20-\x7e]{2,}", data)
                    )
        return tuple(values)

    @staticmethod
    def _spectral_similarity(wav_path, measurement_path):
        with wave.open(str(wav_path), "rb") as stream:
            if stream.getnchannels() != 1:
                return -1.0
            width = stream.getsampwidth()
            rate = stream.getframerate()
            raw = stream.readframes(stream.getnframes())
        samples = MeasurementRepository._pcm_samples(raw, width)
        if len(samples) < 2:
            return -1.0
        frequencies = np.fft.rfftfreq(len(samples), 1.0 / rate)
        magnitude = 20.0 * np.log10(
            np.maximum(np.abs(np.fft.rfft(samples)), 1e-12)
        )
        measured_frequency, measured_spl = (
            MeasurementRepository._text_response(measurement_path)
        )
        if len(measured_frequency) < 3:
            return -1.0
        predicted = np.interp(measured_frequency, frequencies, magnitude)
        predicted -= np.mean(predicted)
        measured_spl -= np.mean(measured_spl)
        if np.std(predicted) == 0.0 or np.std(measured_spl) == 0.0:
            return -1.0
        return float(np.corrcoef(predicted, measured_spl)[0, 1])

    @staticmethod
    def _pcm_samples(raw, width):
        if width == 1:
            return (np.frombuffer(raw, dtype=np.uint8).astype(float) - 128.0) / 128.0
        if width == 2:
            return np.frombuffer(raw, dtype="<i2").astype(float) / 32768.0
        if width == 3:
            data = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
            values = (
                data[:, 0].astype(np.int32)
                | (data[:, 1].astype(np.int32) << 8)
                | (data[:, 2].astype(np.int32) << 16)
            )
            values = np.where(values & 0x800000, values - 0x1000000, values)
            return values.astype(float) / 8388608.0
        if width == 4:
            return np.frombuffer(raw, dtype="<i4").astype(float) / 2147483648.0
        return np.array([], dtype=float)

    @staticmethod
    def _text_response(path):
        frequencies = []
        spl = []
        reading = False
        with Path(path).open("r", encoding="utf-8", errors="ignore") as stream:
            for raw_line in stream:
                line = raw_line.strip()
                if line.startswith(("* Freq(Hz)", "Freq(Hz)")):
                    reading = True
                    continue
                if not reading:
                    continue
                values = line.split()
                if len(values) < 2:
                    continue
                try:
                    frequencies.append(float(values[0]))
                    spl.append(float(values[1]))
                except ValueError:
                    continue
        return np.asarray(frequencies), np.asarray(spl)
