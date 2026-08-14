import pytest

from acousticbrain.application import SBIRProtocolInstanceViewService
from acousticbrain.models import SBIRProtocolInstanceRegistry
from test_sbir_protocol_instance_registry import record


def registry():
    return SBIRProtocolInstanceRegistry().with_record(record())


def test_view_resolves_one_exact_persisted_record_without_mutation():
    value = registry()
    result = SBIRProtocolInstanceViewService().view(
        "sbir-protocol-instance-001",
        registry=value,
    )

    assert result.record is value.records[0]
    assert result.declaration_status == "NOT_DECLARED"
    assert result.execution_status == "NOT_EXECUTED"
    assert result.causality_status == "NOT_ESTABLISHED"
    assert value == registry()


def test_view_rejects_an_unknown_instance_without_reconstruction():
    with pytest.raises(
        ValueError,
        match="SBIR_PROTOCOL_INSTANCE_UNKNOWN: unknown-instance.",
    ):
        SBIRProtocolInstanceViewService().view(
            "unknown-instance",
            registry=registry(),
        )


def test_view_rejects_an_empty_registry_explicitly():
    with pytest.raises(ValueError, match="SBIR_PROTOCOL_INSTANCE_REGISTRY_EMPTY"):
        SBIRProtocolInstanceViewService().view(
            "sbir-protocol-instance-001",
            registry=SBIRProtocolInstanceRegistry(),
        )
