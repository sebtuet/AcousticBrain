from dataclasses import dataclass, replace
from pathlib import Path
import re

from acousticbrain.importers import ExperimentImporter
from acousticbrain.models import (
    ExperimentDescriptor,
    ExperimentFileType,
    ExperimentState,
    ExperimentType,
    EvidenceAcquisitionTestType,
    ImpulseChannel,
)

from .experiment_discovery import ExperimentDiscoveryService


@dataclass(frozen=True)
class CanonicalMeasurementRepresentation:
    experiment_id: str
    selected_files: tuple[str, ...]
    source_files: tuple[str, ...]
    measured_stereo_file: str | None = None
    method: str = "SELECT_REPRESENTATIVE_REPEAT_A"
    representative_selection_derived: bool = True
    stereo_derived: bool = False

    @property
    def derived(self):
        return self.representative_selection_derived


@dataclass(frozen=True)
class ImportedExperiment:
    descriptor: ExperimentDescriptor
    project: object | None
    canonical_representation: CanonicalMeasurementRepresentation | None = None


@dataclass(frozen=True)
class AcousticSession:
    """Session technique auto-ouverte, sans itération métier implicite."""

    measurement_root: str
    experiments: tuple[ImportedExperiment, ...]

    @classmethod
    def auto_open(
        cls,
        path,
        *,
        discovery_service=None,
        importer=None,
        channel_isolation_repeatability_qualifications=(),
    ):
        discovery = discovery_service or ExperimentDiscoveryService()
        experiment_importer = importer or ExperimentImporter()
        descriptors = discovery.discover(path)
        geometry_by_experiment = cls._resolve_geometry(descriptors)
        qualifications = {
            item.provenance.experiment_id: item
            for item in channel_isolation_repeatability_qualifications
        }
        imported = []
        for descriptor in descriptors:
            qualification = qualifications.get(descriptor.experiment_id)
            canonical = cls._canonical_representation(descriptor, qualification)
            import_descriptor = cls._import_descriptor(
                descriptor,
                canonical,
                geometry_by_experiment.get(descriptor.experiment_id),
            )
            imported.append(ImportedExperiment(
                descriptor=descriptor,
                project=cls._load_project(
                    experiment_importer, import_descriptor, canonical
                ),
                canonical_representation=canonical,
            ))
        return cls(measurement_root=str(path), experiments=imported)

    @staticmethod
    def _load_project(importer, descriptor, canonical):
        if descriptor is None:
            return None
        return importer.load(descriptor)

    @staticmethod
    def _canonical_representation(descriptor, qualification):
        if (
            qualification is None
            or qualification.qualification_status.name != "QUALIFIED"
            or not AcousticSession._has_unrepresented_channel_repetitions(descriptor)
        ):
            return None
        source_files = tuple(
            item.relative_path
            for item in descriptor.available_files
            if (
                item.file_type is ExperimentFileType.TXT_MEASUREMENT
                and item.channel in {ImpulseChannel.LEFT, ImpulseChannel.RIGHT}
            )
        )
        stereo_files = tuple(
            item.relative_path
            for item in descriptor.available_files
            if (
                item.file_type is ExperimentFileType.TXT_MEASUREMENT
                and item.channel is ImpulseChannel.STEREO
            )
        )
        selected = tuple(
            path for path in source_files
            if re.search(r"(?:^|[\s_-])A(?:\.txt)?$", Path(path).name, re.IGNORECASE)
        )
        if len(selected) != 2:
            raise ValueError(
                "Qualified repeated experiment requires one representative A "
                "measurement per channel."
            )
        if len(stereo_files) != 1:
            raise ValueError(
                "Qualified native representation requires one measured L+R "
                "measurement."
            )
        return CanonicalMeasurementRepresentation(
            experiment_id=descriptor.experiment_id,
            selected_files=tuple(sorted(selected)),
            source_files=tuple(sorted(source_files)),
            measured_stereo_file=stereo_files[0],
        )

    @staticmethod
    def _import_descriptor(descriptor, canonical, room_description):
        if descriptor.state is not ExperimentState.READY:
            return None
        if canonical is None and AcousticSession._has_unrepresented_channel_repetitions(
            descriptor
        ):
            return None
        if canonical is None:
            return replace(descriptor, room_description=room_description)
        selected = set(canonical.selected_files)
        return replace(
            descriptor,
            available_files=tuple(
                item for item in descriptor.available_files
                if (
                    item.file_type is not ExperimentFileType.TXT_MEASUREMENT
                    or item.relative_path in selected
                    or item.channel is ImpulseChannel.STEREO
                    or item.channel not in {ImpulseChannel.LEFT, ImpulseChannel.RIGHT}
                )
            ),
            room_description=room_description,
        )

    @staticmethod
    def _has_unrepresented_channel_repetitions(descriptor):
        """Keeps declared repeated acquisitions out of the one-response importer."""
        contract = descriptor.evidence_acquisition_plan_contract
        if (
            descriptor.channel_isolation_declaration is None
            or contract is None
            or contract.source_plan.test_type
            is not EvidenceAcquisitionTestType.CHANNEL_ISOLATION
        ):
            return False
        measurement_channels = [
            item.channel
            for item in descriptor.available_files
            if (
                item.file_type is ExperimentFileType.TXT_MEASUREMENT
                and item.channel in {ImpulseChannel.LEFT, ImpulseChannel.RIGHT}
            )
        ]
        return any(measurement_channels.count(channel) > 1 for channel in (
            ImpulseChannel.LEFT,
            ImpulseChannel.RIGHT,
        ))

    @classmethod
    def _resolve_geometry(cls, descriptors):
        by_id = {item.experiment_id: item for item in descriptors}
        resolved = {}
        for descriptor in descriptors:
            local = descriptor.room_description
            declaration = descriptor.experiment_declaration
            reference_id = declaration.reference_experiment_code
            reference = by_id.get(reference_id) if reference_id is not None else None
            inherited = (
                reference.room_description
                if reference is not None
                and cls._geometry_controls_are_explicit(
                    declaration.controlled_variables
                )
                else None
            )
            if (
                local is not None
                and inherited is not None
                and cls._geometry_values(local) != cls._geometry_values(inherited)
            ):
                raise ValueError(
                    "Controlled manifest geometry conflicts with explicit "
                    f"reference: {descriptor.experiment_id} -> {reference_id}."
                )
            if local is not None:
                resolved[descriptor.experiment_id] = local
            elif inherited is not None:
                resolved[descriptor.experiment_id] = inherited
        return resolved

    @staticmethod
    def _geometry_controls_are_explicit(controlled_variables):
        values = set(controlled_variables)
        return (
            {"ROOM_CONFIGURATION", "LOUDSPEAKER_POSITION"}.issubset(values)
            and bool(
                {"LISTENING_POSITION", "MICROPHONE_POSITION"} & values
            )
        )

    @staticmethod
    def _geometry_values(description):
        return (
            description.dimensions,
            description.speakers,
            description.listening_positions,
        )

    @property
    def descriptors(self):
        return tuple(item.descriptor for item in self.experiments)

    @property
    def baseline(self):
        return next(
            (
                item
                for item in self.experiments
                if item.descriptor.experiment_type is ExperimentType.BASELINE
            ),
            None,
        )

    @property
    def current_project(self):
        ready_experiments = [
            item.project
            for item in self.experiments
            if item.project is not None
            and item.descriptor.experiment_type is ExperimentType.EXPERIMENT
        ]
        if ready_experiments:
            return ready_experiments[-1]
        return self.baseline.project if self.baseline is not None else None
