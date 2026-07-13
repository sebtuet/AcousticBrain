import re
from datetime import datetime, timezone
from pathlib import Path

from acousticbrain.models import (
    ExperimentDescriptor,
    ExperimentFileDescriptor,
    ExperimentFileType,
    ExperimentState,
    ExperimentType,
    ImpulseChannel,
)
from acousticbrain.persistence import MeasurementRepository


class ExperimentDiscoveryService:
    """Découvre les expériences et maintient leurs manifests techniques."""

    SCHEMA_VERSION = 1
    EXPERIMENT_PATTERN = re.compile(r"^exp-\d+(?:[-_].*)?$", re.IGNORECASE)
    REQUIRED_CHANNELS = {
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
        ImpulseChannel.STEREO,
    }

    def __init__(self, repository=None, clock=None):
        self.repository = repository or MeasurementRepository()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def discover(self, measurement_root) -> tuple[ExperimentDescriptor, ...]:
        descriptors = [
            self._descriptor(directory)
            for directory in self.repository.list_directories(measurement_root)
            if self._experiment_type(directory.name) is not None
        ]
        return tuple(sorted(descriptors, key=self._sort_key))

    def _descriptor(self, directory):
        directory = Path(directory)
        experiment_type = self._experiment_type(directory.name)
        existing = self.repository.load_manifest(directory) or {}
        assignments = existing.get("channel_assignments", {})
        if not isinstance(assignments, dict):
            assignments = {}
        inspected = self.repository.inspect_directory(
            directory,
            channel_assignments=assignments,
        )
        inspected = self.repository.associate_wav_channels(inspected)
        content_hash = self.repository.aggregate_hash(inspected)
        channels = tuple(
            sorted(
                {item.channel for item in inspected if item.channel is not None},
                key=lambda item: item.value,
            )
        )
        measurement_channels = {
            item.channel
            for item in inspected
            if item.file_type is ExperimentFileType.TXT_MEASUREMENT
            and item.channel is not None
        }
        state = (
            ExperimentState.READY
            if self.REQUIRED_CHANNELS.issubset(measurement_channels)
            else ExperimentState.INCOMPLETE
        )
        timestamp = self._timestamp(directory, inspected, existing)
        imported_at = existing.get("imported_at")
        if not isinstance(imported_at, str) or not imported_at:
            imported_at = self.clock().isoformat()
        detected_assignments = {
            item.path.relative_to(directory).as_posix(): item.channel.value
            for item in inspected
            if item.channel is not None
        }
        manifest = {
            "schema_version": self.SCHEMA_VERSION,
            "experiment_id": directory.name,
            "experiment_type": experiment_type.value,
            "timestamp": timestamp,
            "imported_at": imported_at,
            "state": state.value,
            "content_hash": content_hash,
            "channel_assignments": detected_assignments,
            "files": [
                {
                    "path": item.path.relative_to(directory).as_posix(),
                    "type": item.file_type.value,
                    "sha256": item.sha256,
                    "channel": item.channel.value if item.channel else None,
                }
                for item in inspected
            ],
        }
        self.repository.save_manifest(directory, manifest)
        files = tuple(
            ExperimentFileDescriptor(
                relative_path=item.path.relative_to(directory).as_posix(),
                file_type=item.file_type,
                sha256=item.sha256,
                channel=item.channel,
            )
            for item in inspected
        )
        wav_files = tuple(
            item.relative_path
            for item in files
            if item.file_type is ExperimentFileType.WAV
        )
        txt_files = tuple(
            item.relative_path
            for item in files
            if item.file_type in {
                ExperimentFileType.TXT_MEASUREMENT,
                ExperimentFileType.TXT_IMPULSE,
                ExperimentFileType.TXT_UNKNOWN,
            }
        )
        mdat_files = tuple(
            item.relative_path
            for item in files
            if item.file_type is ExperimentFileType.MDAT
        )
        return ExperimentDescriptor(
            experiment_id=directory.name,
            directory=str(directory.resolve()),
            experiment_type=experiment_type,
            available_files=files,
            available_channels=channels,
            wav_files=wav_files,
            txt_files=txt_files,
            mdat_file=mdat_files[0] if mdat_files else None,
            manifest_present=True,
            content_hash=content_hash,
            timestamp=timestamp,
            imported_at=imported_at,
            state=state,
        )

    @classmethod
    def _experiment_type(cls, name):
        if name.lower() == "baseline":
            return ExperimentType.BASELINE
        if cls.EXPERIMENT_PATTERN.fullmatch(name):
            return ExperimentType.EXPERIMENT
        return None

    @staticmethod
    def _timestamp(directory, inspected, existing):
        timestamps = sorted(
            item.timestamp for item in inspected if item.timestamp is not None
        )
        if timestamps:
            return timestamps[0]
        existing_timestamp = existing.get("timestamp")
        if isinstance(existing_timestamp, str) and existing_timestamp:
            return existing_timestamp
        if inspected:
            return min(
                MeasurementRepository.file_timestamp(item.path)
                for item in inspected
            )
        return MeasurementRepository.file_timestamp(directory)

    @staticmethod
    def _sort_key(descriptor):
        return (
            descriptor.experiment_type is not ExperimentType.BASELINE,
            descriptor.timestamp,
            descriptor.experiment_id,
        )
