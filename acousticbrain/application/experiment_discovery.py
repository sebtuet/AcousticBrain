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
    CausalProtocolStep,
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
        comparison_metadata = self._comparison_metadata(existing)
        causal_step = self._causal_step(existing, directory.name)
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
        if comparison_metadata:
            manifest["comparison"] = comparison_metadata
        if causal_step is not None:
            manifest["causal_protocol_step"] = {
                "protocol_code": causal_step.protocol_code,
                "step_code": causal_step.step_code,
                "step_index": causal_step.step_index,
                "controlled_variable_codes": list(
                    causal_step.controlled_variable_codes
                ),
                "changed_variable_codes": list(causal_step.changed_variable_codes),
                "unknown_variable_codes": list(causal_step.unknown_variable_codes),
                "observation_codes": list(causal_step.observation_codes),
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
            parent_experiment_ids=self._string_tuple(
                comparison_metadata.get("parent_experiment_ids")
            ),
            source_protocol_id=self._optional_string(
                comparison_metadata.get("source_protocol_id")
            ),
            source_hypothesis_code=self._optional_string(
                comparison_metadata.get("source_hypothesis_code")
            ),
            declared_change_codes=self._string_tuple(
                comparison_metadata.get("declared_change_codes")
            ),
            required_comparison_fact_codes=self._string_tuple(
                comparison_metadata.get("required_fact_codes")
            ),
            causal_protocol_step=causal_step,
        )

    @classmethod
    def _causal_step(cls, manifest, experiment_id):
        value = manifest.get("causal_protocol_step")
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError("Causal protocol step manifest entry must be an object.")
        protocol_code = cls._optional_string(value.get("protocol_code"))
        step_code = cls._optional_string(value.get("step_code"))
        step_index = value.get("step_index")
        if protocol_code is None or step_code is None:
            raise ValueError("Causal protocol and step codes are required.")
        return CausalProtocolStep(
            protocol_code=protocol_code,
            step_code=step_code,
            step_index=step_index,
            experiment_id=experiment_id,
            controlled_variable_codes=cls._string_tuple(
                value.get("controlled_variable_codes")
            ),
            changed_variable_codes=cls._string_tuple(
                value.get("changed_variable_codes")
            ),
            unknown_variable_codes=cls._string_tuple(
                value.get("unknown_variable_codes")
            ),
            observation_codes=cls._string_tuple(value.get("observation_codes")),
        )

    @classmethod
    def _comparison_metadata(cls, manifest):
        value = manifest.get("comparison", {})
        if not isinstance(value, dict):
            return {}
        metadata = {}
        parents = value.get("parent_experiment_ids", value.get("parent_experiment_id"))
        parent_ids = cls._string_tuple(parents)
        if parent_ids:
            metadata["parent_experiment_ids"] = list(parent_ids)
        for key in ("source_protocol_id", "source_hypothesis_code"):
            item = cls._optional_string(value.get(key))
            if item is not None:
                metadata[key] = item
        changes = cls._string_tuple(value.get("declared_change_codes"))
        if changes:
            metadata["declared_change_codes"] = list(changes)
        required = cls._string_tuple(value.get("required_fact_codes"))
        if required:
            metadata["required_fact_codes"] = list(required)
        return metadata

    @staticmethod
    def _optional_string(value):
        return value.strip() if isinstance(value, str) and value.strip() else None

    @classmethod
    def _string_tuple(cls, value):
        if isinstance(value, str):
            value = (value,)
        if not isinstance(value, (list, tuple)):
            return ()
        return tuple(dict.fromkeys(
            item for raw in value
            if (item := cls._optional_string(raw)) is not None
        ))

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
