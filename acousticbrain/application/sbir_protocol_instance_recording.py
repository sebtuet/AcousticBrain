from dataclasses import dataclass

from acousticbrain.models import (
    SBIRProtocolInstanceCompatibility,
    SBIRProtocolInstanceRecord,
)
from acousticbrain.persistence import SBIRProtocolInstanceRegistryJsonRepository


@dataclass(frozen=True)
class SBIRProtocolInstanceRecordingResult:
    record: SBIRProtocolInstanceRecord
    registry_path: str
    persisted: bool


class SBIRProtocolInstanceRecordingService:
    def __init__(self, repository=None):
        self.repository = repository or SBIRProtocolInstanceRegistryJsonRepository()

    def record(self, compatibility, *, registry_path):
        if not isinstance(compatibility, SBIRProtocolInstanceCompatibility):
            raise TypeError("SBIRProtocolInstanceCompatibility is required.")
        record = SBIRProtocolInstanceRecord.from_compatibility(compatibility)
        registry = self.repository.load(registry_path)
        updated = registry.with_record(record)
        persisted = self.repository.save(registry_path, updated)
        return SBIRProtocolInstanceRecordingResult(
            record=record,
            registry_path=str(registry_path),
            persisted=persisted,
        )
