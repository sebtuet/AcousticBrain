from dataclasses import dataclass, replace

from acousticbrain.importers import ExperimentImporter
from acousticbrain.models import ExperimentDescriptor, ExperimentState, ExperimentType

from .experiment_discovery import ExperimentDiscoveryService


@dataclass(frozen=True)
class ImportedExperiment:
    descriptor: ExperimentDescriptor
    project: object | None


@dataclass(frozen=True)
class AcousticSession:
    """Session technique auto-ouverte, sans itération métier implicite."""

    measurement_root: str
    experiments: tuple[ImportedExperiment, ...]

    @classmethod
    def auto_open(cls, path, *, discovery_service=None, importer=None):
        discovery = discovery_service or ExperimentDiscoveryService()
        experiment_importer = importer or ExperimentImporter()
        descriptors = discovery.discover(path)
        geometry_by_experiment = cls._resolve_geometry(descriptors)
        imported = tuple(
            ImportedExperiment(
                descriptor=descriptor,
                project=(
                    experiment_importer.load(replace(
                        descriptor,
                        room_description=geometry_by_experiment.get(
                            descriptor.experiment_id
                        ),
                    ))
                    if descriptor.state is ExperimentState.READY
                    else None
                ),
            )
            for descriptor in descriptors
        )
        return cls(measurement_root=str(path), experiments=imported)

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
