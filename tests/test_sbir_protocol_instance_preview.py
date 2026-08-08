from dataclasses import replace

import pytest

from acousticbrain.application import SBIRProtocolInstancePreviewService
from acousticbrain.models import SBIRProtocolInstanceRegistry
from test_sbir_protocol_instance_compatibility import proposal
from test_sbir_protocol_instance_registry import record
from test_sbir_protocol_instance_resolution import (
    PROTOCOL_ID,
    experiment,
    geometry_candidate,
    protocol_input,
    source_plan,
)


def preview(input_value=None, registry=None, **overrides):
    plan_value = source_plan()
    arguments = {
        "plans": (plan_value,),
        "protocol_ids": (PROTOCOL_ID,),
        "experiments": (experiment("baseline"), experiment("exp-sbir-001")),
        "geometry_candidates": (geometry_candidate(),),
        "displacement_proposals": (proposal(),),
        "registry": registry or SBIRProtocolInstanceRegistry(),
    }
    arguments.update(overrides)
    return SBIRProtocolInstancePreviewService().preview(
        input_value or protocol_input(plan_value),
        **arguments,
    )


def test_preview_projects_complete_record_without_recording():
    registry = SBIRProtocolInstanceRegistry()
    result = preview(registry=registry)
    assert result.registry_state == "NOT_RECORDED"
    assert result.record.compatibility_decisions[-1].value == (
        "PROTOCOL_INSTANCE_COMPATIBLE"
    )
    assert registry.records == ()


def test_identical_record_is_reported_without_mutation():
    existing = record()
    registry = SBIRProtocolInstanceRegistry().with_record(existing)
    result = preview(
        input_value=existing.protocol_instance_input,
        registry=registry,
    )
    assert result.registry_state == "ALREADY_RECORDED"
    assert result.record == existing
    assert registry.records == (existing,)


def test_divergent_identity_is_rejected_without_mutation():
    existing = record()
    registry = SBIRProtocolInstanceRegistry().with_record(existing)
    divergent = replace(
        existing.protocol_instance_input,
        user_note="Different declaration",
    )
    before = registry
    with pytest.raises(ValueError, match="SBIR_PROTOCOL_INSTANCE_DIVERGENT"):
        preview(input_value=divergent, registry=registry)
    assert registry is before


def test_failed_compatibility_does_not_touch_registry():
    registry = SBIRProtocolInstanceRegistry()
    with pytest.raises(ValueError, match="DISPLACEMENT_SOURCE_MISMATCH"):
        preview(
            registry=registry,
            displacement_proposals=(proposal(step_distance_m=0.10),),
        )
    assert registry.records == ()
