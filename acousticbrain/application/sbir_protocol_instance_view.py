from dataclasses import dataclass

from acousticbrain.models import (
    SBIRProtocolInstanceRecord,
    SBIRProtocolInstanceRegistry,
)


@dataclass(frozen=True)
class SBIRProtocolInstanceView:
    """Exact read-only projection of one persisted SBIR protocol instance."""

    record: SBIRProtocolInstanceRecord
    declaration_status: str = "NOT_DECLARED"
    execution_status: str = "NOT_EXECUTED"
    causality_status: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        if not isinstance(self.record, SBIRProtocolInstanceRecord):
            raise TypeError("SBIR protocol-instance view requires a record.")
        if self.declaration_status != "NOT_DECLARED":
            raise ValueError("SBIR protocol-instance view cannot declare an experiment.")
        if self.execution_status != "NOT_EXECUTED":
            raise ValueError("SBIR protocol-instance view cannot execute an experiment.")
        if self.causality_status != "NOT_ESTABLISHED":
            raise ValueError("SBIR protocol-instance view cannot establish causality.")


class SBIRProtocolInstanceViewService:
    """Resolves one exact immutable registry record without source re-analysis."""

    def view(self, protocol_instance_id, *, registry):
        if not isinstance(protocol_instance_id, str) or (
            not protocol_instance_id
            or protocol_instance_id != protocol_instance_id.strip()
        ):
            raise ValueError(
                "SBIR_PROTOCOL_INSTANCE_ID_INVALID: expected exact non-empty text."
            )
        if not isinstance(registry, SBIRProtocolInstanceRegistry):
            raise TypeError("SBIRProtocolInstanceRegistry is required.")
        if not registry.records:
            raise ValueError("SBIR_PROTOCOL_INSTANCE_REGISTRY_EMPTY.")
        matches = tuple(
            record
            for record in registry.records
            if record.protocol_instance_input.protocol_instance_id
            == protocol_instance_id
        )
        if not matches:
            raise ValueError(
                "SBIR_PROTOCOL_INSTANCE_UNKNOWN: " + protocol_instance_id + "."
            )
        if len(matches) != 1:
            raise ValueError(
                "SBIR_PROTOCOL_INSTANCE_AMBIGUOUS: " + protocol_instance_id + "."
            )
        return SBIRProtocolInstanceView(record=matches[0])
