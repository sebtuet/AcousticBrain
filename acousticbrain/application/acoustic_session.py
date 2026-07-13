from dataclasses import dataclass

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
        imported = tuple(
            ImportedExperiment(
                descriptor=descriptor,
                project=(
                    experiment_importer.load(descriptor)
                    if descriptor.state is ExperimentState.READY
                    else None
                ),
            )
            for descriptor in descriptors
        )
        return cls(measurement_root=str(path), experiments=imported)

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
