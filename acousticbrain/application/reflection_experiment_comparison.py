from acousticbrain.models import ControlledReflectionExperimentComparisonRegistry
from acousticbrain.persistence import (
    ControlledReflectionExperimentComparisonJsonRepository,
)


class ControlledReflectionExperimentComparisonService:
    def __init__(self, repository=None):
        self.repository = (
            repository or ControlledReflectionExperimentComparisonJsonRepository()
        )

    def save(self, path, comparisons):
        registry = ControlledReflectionExperimentComparisonRegistry(
            tuple(comparisons)
        )
        self.repository.save(path, registry)
        return registry

    def load(self, path):
        return self.repository.load(path)

    def load_into_project(self, project, path):
        registry = self.load(path)
        project.controlled_reflection_experiment_comparisons = registry.comparisons
        return registry
