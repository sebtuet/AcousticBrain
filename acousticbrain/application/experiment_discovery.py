import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from acousticbrain.models import (
    CausalDiscriminationDecision,
    CausalDiscriminationDecisionReason,
    CausalDiscriminationDecisionStatus,
    ExperimentDescriptor,
    ExperimentFileDescriptor,
    ExperimentFileType,
    ExperimentState,
    ExperimentType,
    ExperimentDeclaration,
    ExperimentKind,
    ImpulseChannel,
    ListeningPosition,
    RoomDescription,
    RoomDimensions,
    SpeakerPosition,
    CausalProtocolStep,
    ChannelIsolationDeclaration,
    ChannelIsolationMeasurementResult,
    ChannelIsolationResultDeclaration,
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
        declaration = self._experiment_declaration(existing)
        if (
            declaration.experiment_kind is not ExperimentKind.UNKNOWN
            and declaration.reference_experiment_code
            and "parent_experiment_ids" not in comparison_metadata
        ):
            comparison_metadata["parent_experiment_ids"] = [
                declaration.reference_experiment_code
            ]
        causal_step = self._causal_step(existing, directory.name)
        causal_decisions = self._causal_decisions(existing, directory.name)
        detected_assignments = {
            item.path.relative_to(directory).as_posix(): item.channel.value
            for item in inspected
            if item.channel is not None
        }
        existing_files_by_path = self._existing_files_by_path(existing)
        serialized_files = []
        for item in inspected:
            relative_path = item.path.relative_to(directory).as_posix()
            serialized_file = dict(
                existing_files_by_path.get(relative_path, {})
            )
            serialized_file.update(
                {
                    "path": relative_path,
                    "type": item.file_type.value,
                    "sha256": item.sha256,
                    "channel": item.channel.value if item.channel else None,
                }
            )
            serialized_files.append(serialized_file)
        manifest = dict(existing)
        manifest.update(
            {
                "schema_version": self.SCHEMA_VERSION,
                "experiment_id": directory.name,
                "experiment_type": experiment_type.value,
                "timestamp": timestamp,
                "imported_at": imported_at,
                "state": state.value,
                "content_hash": content_hash,
                "channel_assignments": detected_assignments,
                "files": serialized_files,
            }
        )
        if comparison_metadata:
            comparison = dict(existing.get("comparison", {}))
            for key in (
                "parent_experiment_id",
                "parent_experiment_ids",
                "source_protocol_id",
                "source_hypothesis_code",
                "declared_change_codes",
                "required_fact_codes",
                "parameters",
            ):
                comparison.pop(key, None)
            comparison.update(comparison_metadata)
            manifest["comparison"] = comparison
        if declaration.experiment_kind is not ExperimentKind.UNKNOWN:
            experiment_declaration = dict(
                existing.get("experiment_declaration", {})
            )
            experiment_declaration.update(self._serialize_declaration(declaration))
            manifest["experiment_declaration"] = experiment_declaration
        if causal_step is not None:
            causal_protocol_step = dict(existing.get("causal_protocol_step", {}))
            causal_protocol_step.update(
                {
                    "protocol_code": causal_step.protocol_code,
                    "step_code": causal_step.step_code,
                    "step_index": causal_step.step_index,
                    "controlled_variable_codes": list(
                        causal_step.controlled_variable_codes
                    ),
                    "changed_variable_codes": list(
                        causal_step.changed_variable_codes
                    ),
                    "unknown_variable_codes": list(
                        causal_step.unknown_variable_codes
                    ),
                    "observation_codes": list(causal_step.observation_codes),
                }
            )
            manifest["causal_protocol_step"] = causal_protocol_step
        if causal_decisions:
            existing_decisions = {
                self._optional_string(item.get("discrimination_code")): item
                for item in existing.get("causal_discrimination_decisions", [])
            }
            serialized_decisions = []
            for item in causal_decisions:
                serialized = dict(existing_decisions[item.discrimination_code])
                serialized.update(
                    {
                        "protocol_code": item.protocol_code,
                        "discrimination_code": item.discrimination_code,
                        "status": item.status.value,
                        "reason": item.reason.value,
                    }
                )
                serialized_decisions.append(serialized)
            manifest["causal_discrimination_decisions"] = serialized_decisions
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
            comparison_parameters=tuple(
                sorted(comparison_metadata.get("parameters", {}).items())
            ),
            causal_protocol_step=causal_step,
            causal_discrimination_decisions=causal_decisions,
            experiment_declaration=declaration,
            source_evidence_acquisition_plan_id=(
                self._source_evidence_acquisition_plan_id(existing)
            ),
            channel_isolation_declaration=(
                self._channel_isolation_declaration(existing)
            ),
            channel_isolation_result_declaration=(
                self._channel_isolation_result_declaration(existing)
            ),
            room_description=self._room_description(existing, directory.name),
        )

    @classmethod
    def _existing_files_by_path(cls, manifest):
        values = manifest.get("files", [])
        if not isinstance(values, list):
            return {}
        files_by_path = {}
        for value in values:
            if not isinstance(value, dict):
                continue
            path = cls._optional_string(value.get("path"))
            if path is None:
                continue
            if path in files_by_path:
                raise ValueError("Manifest file paths must be unique.")
            files_by_path[path] = value
        return files_by_path

    @classmethod
    def _experiment_declaration(cls, manifest):
        value = manifest.get("experiment_declaration")
        if value is None:
            return ExperimentDeclaration.unknown()
        if not isinstance(value, dict):
            raise ValueError("Experiment declaration manifest entry must be an object.")
        try:
            kind = ExperimentKind(value.get("experiment_kind"))
        except ValueError as error:
            raise ValueError("Unsupported experiment kind.") from error
        provenance = value.get("field_provenance", {})
        if not isinstance(provenance, dict):
            raise ValueError("Experiment declaration provenance must be an object.")
        return ExperimentDeclaration(
            schema_version=value.get("schema_version"),
            experiment_kind=kind,
            reference_experiment_code=cls._optional_string(
                value.get("reference_experiment_code")
            ),
            modified_variables=tuple(sorted(cls._string_tuple(
                value.get("modified_variables")
            ))),
            controlled_variables=tuple(sorted(cls._string_tuple(
                value.get("controlled_variables")
            ))),
            user_note=cls._optional_string(value.get("user_note")),
            field_provenance=tuple(sorted(
                (key, source)
                for key, raw_source in provenance.items()
                if isinstance(key, str)
                and key
                and (source := cls._optional_string(raw_source)) is not None
            )),
        )

    @classmethod
    def _room_description(cls, manifest, experiment_id):
        keys = ("coordinate_system", "room", "loudspeakers", "listening_position")
        values = tuple(manifest.get(key) for key in keys)
        if all(value is None for value in values):
            return None
        if any(value is None for value in values):
            return None
        if any(not isinstance(value, dict) for value in values):
            raise ValueError(f"Manifest geometry is invalid for {experiment_id}.")

        coordinate_system, room, loudspeakers, listening_position = values
        if coordinate_system.get("unit") != "m":
            raise ValueError("Manifest geometry coordinate unit must be m.")
        for key in (
            "origin",
            "x_axis",
            "y_axis",
            "z_axis",
        ):
            if cls._optional_string(coordinate_system.get(key)) is None:
                raise ValueError(
                    f"Manifest geometry coordinate system is incomplete: {key}."
                )

        dimensions = cls._geometry_object(room, "dimensions")
        left = cls._geometry_object(loudspeakers, "left")
        right = cls._geometry_object(loudspeakers, "right")
        listening = cls._geometry_object(listening_position, "position")
        return RoomDescription(
            name=f"Manifest geometry for {experiment_id}",
            dimensions=RoomDimensions(
                length_m=cls._geometry_number(dimensions, "length"),
                width_m=cls._geometry_number(dimensions, "width"),
                height_m=cls._geometry_number(dimensions, "height"),
            ),
            speakers=(
                cls._speaker_position("LEFT", left),
                cls._speaker_position("RIGHT", right),
            ),
            listening_positions=(
                ListeningPosition(
                    position_id="LISTENING_POSITION",
                    x_m=cls._geometry_number(listening, "x"),
                    y_m=cls._geometry_number(listening, "y"),
                    z_m=cls._geometry_number(listening, "z"),
                ),
            ),
        )

    @staticmethod
    def _geometry_object(value, key):
        item = value.get(key)
        if not isinstance(item, dict):
            raise ValueError(f"Manifest geometry object is missing: {key}.")
        return item

    @classmethod
    def _speaker_position(cls, speaker_id, value):
        position = cls._geometry_object(value, "position")
        return SpeakerPosition(
            speaker_id=speaker_id,
            x_m=cls._geometry_number(position, "x"),
            y_m=cls._geometry_number(position, "y"),
            z_m=cls._geometry_number(position, "z"),
        )

    @staticmethod
    def _geometry_number(value, key):
        item = value.get(key)
        if not isinstance(item, (int, float)) or isinstance(item, bool):
            raise ValueError(f"Manifest geometry value is missing: {key}.")
        return float(item)

    @staticmethod
    def _serialize_declaration(declaration):
        return {
            "schema_version": declaration.schema_version,
            "experiment_kind": declaration.experiment_kind.value,
            "reference_experiment_code": declaration.reference_experiment_code,
            "modified_variables": list(declaration.modified_variables),
            "controlled_variables": list(declaration.controlled_variables),
            "user_note": declaration.user_note,
            "field_provenance": dict(declaration.field_provenance),
        }

    @classmethod
    def _causal_decisions(cls, manifest, experiment_id):
        values = manifest.get("causal_discrimination_decisions", [])
        if not isinstance(values, list):
            raise ValueError(
                "Causal discrimination decisions manifest entry must be a list."
            )
        decisions = []
        for value in values:
            if not isinstance(value, dict):
                raise ValueError("Causal discrimination decision must be an object.")
            protocol_code = cls._optional_string(value.get("protocol_code"))
            discrimination_code = cls._optional_string(
                value.get("discrimination_code")
            )
            if protocol_code is None or discrimination_code is None:
                raise ValueError("Causal discrimination decision codes are required.")
            try:
                status = CausalDiscriminationDecisionStatus(value.get("status"))
                reason = CausalDiscriminationDecisionReason(value.get("reason"))
            except ValueError as error:
                raise ValueError(
                    "Unsupported causal discrimination decision status or reason."
                ) from error
            decisions.append(CausalDiscriminationDecision(
                protocol_code=protocol_code,
                discrimination_code=discrimination_code,
                status=status,
                reason=reason,
                experiment_id=experiment_id,
            ))
        if len({item.discrimination_code for item in decisions}) != len(decisions):
            raise ValueError("Causal discrimination decisions must be unique.")
        return tuple(decisions)

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
        parameters = value.get("parameters", {})
        if not isinstance(parameters, dict):
            raise ValueError("Experiment comparison parameters must be an object.")
        if any(
            not isinstance(key, str)
            or not key
            or not isinstance(item, (str, int, float, bool))
            for key, item in parameters.items()
        ):
            raise ValueError("Experiment comparison parameters are invalid.")
        if parameters:
            metadata["parameters"] = {
                key: parameters[key] for key in sorted(parameters)
            }
        return metadata

    @staticmethod
    def _optional_string(value):
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _source_evidence_acquisition_plan_id(manifest):
        if "source_evidence_acquisition_plan_id" not in manifest:
            return None
        value = manifest["source_evidence_acquisition_plan_id"]
        if value is None:
            return None
        if not isinstance(value, str) or not value:
            raise ValueError(
                "Source evidence acquisition plan id must be absent or non-empty."
            )
        return value

    @classmethod
    def _channel_isolation_declaration(cls, manifest):
        value = manifest.get("channel_isolation_declaration")
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError(
                "Channel isolation declaration manifest entry must be an object."
            )
        repeated_values = cls._exact_string_tuple(
            value.get("repeated_channels", ())
        )
        try:
            repeated_channels = tuple(
                sorted(
                    (ImpulseChannel(item) for item in repeated_values),
                    key=lambda item: item.value,
                )
            )
        except ValueError as error:
            raise ValueError(
                "Channel isolation repeated channels are invalid."
            ) from error
        if any(
            channel not in (ImpulseChannel.LEFT, ImpulseChannel.RIGHT)
            for channel in repeated_channels
        ):
            raise ValueError(
                "Channel isolation repetitions support LEFT and RIGHT only."
            )
        return ChannelIsolationDeclaration(
            repeated_channels=repeated_channels,
            available_inputs=tuple(sorted(cls._exact_string_tuple(
                value.get("available_inputs", ())
            ))),
            controlled_variables=tuple(sorted(cls._exact_string_tuple(
                value.get("controlled_variables", ())
            ))),
            independent_variables=tuple(sorted(cls._exact_string_tuple(
                value.get("independent_variables", ())
            ))),
            measurements=tuple(sorted(cls._exact_string_tuple(
                value.get("measurements", ())
            ))),
        )

    @staticmethod
    def _exact_string_tuple(value):
        if not isinstance(value, (list, tuple)):
            raise ValueError(
                "Channel isolation declaration collections must be lists."
            )
        if any(not isinstance(item, str) or not item for item in value):
            raise ValueError(
                "Channel isolation declaration values must be non-empty strings."
            )
        if len(value) != len(set(value)):
            raise ValueError(
                "Channel isolation declaration values must be unique."
            )
        return tuple(value)

    @classmethod
    def _channel_isolation_result_declaration(cls, manifest):
        value = manifest.get("channel_isolation_results")
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError(
                "Channel isolation results manifest entry must be an object."
            )
        measurements = value.get("measurements", ())
        if not isinstance(measurements, list):
            raise ValueError(
                "Channel isolation result measurements must be a list."
            )
        parsed = []
        for measurement in measurements:
            if not isinstance(measurement, dict):
                raise ValueError(
                    "Channel isolation measurement results must be objects."
                )
            result_id = measurement.get("result_id")
            raw_value = measurement.get("value")
            unit = measurement.get("unit")
            if not isinstance(result_id, str) or not result_id:
                raise ValueError(
                    "Channel isolation result ids must be non-empty strings."
                )
            if not isinstance(raw_value, str) or not raw_value:
                raise ValueError(
                    "Channel isolation result values must be decimal strings."
                )
            if unit is not None and (
                not isinstance(unit, str) or not unit
            ):
                raise ValueError(
                    "Channel isolation result units must be absent or non-empty."
                )
            try:
                decimal_value = Decimal(raw_value)
            except InvalidOperation as error:
                raise ValueError(
                    "Channel isolation result values must be valid decimals."
                ) from error
            parsed.append(ChannelIsolationMeasurementResult(
                result_id=result_id,
                value=decimal_value,
                unit=unit,
            ))
        return ChannelIsolationResultDeclaration(
            measurements=tuple(sorted(
                parsed,
                key=lambda item: (
                    item.result_id,
                    item.value,
                    item.unit or "",
                ),
            )),
        )

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
