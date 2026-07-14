from acousticbrain.models import ControlledReflectionHypothesisStatusUpdateRegistry
from acousticbrain.persistence import ControlledReflectionHypothesisStatusJsonRepository


class ControlledReflectionHypothesisStatusUpdateService:
    def __init__(self, repository=None):
        self.repository = repository or ControlledReflectionHypothesisStatusJsonRepository()

    def save(self, path, updates):
        registry = ControlledReflectionHypothesisStatusUpdateRegistry(tuple(updates))
        self.repository.save(path, registry)
        return registry

    def load(self, path):
        return self.repository.load(path)

    def load_into_project(self, project, path):
        registry = self.load(path)
        project.controlled_reflection_hypothesis_status_updates = registry.updates
        return registry
