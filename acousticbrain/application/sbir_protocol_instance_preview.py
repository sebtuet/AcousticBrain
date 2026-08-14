from dataclasses import dataclass

from acousticbrain.models import (
    SBIRProtocolInstanceRecord,
    SBIRProtocolInstanceRegistry,
)

from .sbir_protocol_instance_compatibility import (
    SBIRProtocolInstanceCompatibilityValidator,
)
from .sbir_protocol_instance_resolution import SBIRProtocolInstanceResolver


@dataclass(frozen=True)
class SBIRProtocolInstancePreviewResult:
    record: SBIRProtocolInstanceRecord
    registry_state: str

    def __post_init__(self):
        if not isinstance(self.record, SBIRProtocolInstanceRecord):
            raise TypeError("SBIR protocol-instance preview requires a record.")
        if self.registry_state not in ("NOT_RECORDED", "ALREADY_RECORDED"):
            raise ValueError("SBIR protocol-instance preview state is invalid.")


class SBIRProtocolInstancePreviewService:
    """Projects exact resolution, compatibility and registry state without writing."""

    def __init__(self, resolver=None, validator=None):
        self.resolver = resolver or SBIRProtocolInstanceResolver()
        self.validator = validator or SBIRProtocolInstanceCompatibilityValidator()

    def preview(
        self,
        protocol_instance_input,
        *,
        plans,
        protocol_ids,
        experiments,
        geometry_candidates,
        displacement_proposals,
        registry,
    ):
        if not isinstance(registry, SBIRProtocolInstanceRegistry):
            raise TypeError("SBIRProtocolInstanceRegistry is required.")
        resolution = self.resolver.resolve(
            protocol_instance_input,
            plans=plans,
            protocol_ids=protocol_ids,
            experiments=experiments,
            geometry_candidates=geometry_candidates,
        )
        compatibility = self.validator.validate(
            resolution,
            displacement_proposals=displacement_proposals,
        )
        record = SBIRProtocolInstanceRecord.from_compatibility(compatibility)
        updated = registry.with_record(record)
        return SBIRProtocolInstancePreviewResult(
            record=record,
            registry_state=(
                "ALREADY_RECORDED" if updated is registry else "NOT_RECORDED"
            ),
        )
