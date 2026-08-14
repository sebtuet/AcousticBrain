from dataclasses import replace

import pytest

from acousticbrain.application import EvidencePlanPreparationPreviewService
from acousticbrain.models import (
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan


def preview_record(*statuses):
    return record(*statuses)


def test_unknown_statuses_project_separate_decisions_without_recording():
    source = preview_record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    registry = EvidencePlanPreparationRegistry()
    result = EvidencePlanPreparationPreviewService().preview(
        source.confirmation_input, plans=(ready_plan(),), registry=registry
    )
    assert result.registry_state == "NOT_RECORDED"
    assert result.record.resolution_status.value == "PLAN_EXACTLY_RESOLVED"
    assert result.record.declaration_status.value == "PREPARATION_DECLARED"
    assert result.record.all_prerequisites_status is None
    assert registry == EvidencePlanPreparationRegistry()


def test_all_confirmed_projects_user_confirmation_without_verification():
    source = preview_record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    result = EvidencePlanPreparationPreviewService().preview(
        source.confirmation_input,
        plans=(ready_plan(),),
        registry=EvidencePlanPreparationRegistry(),
    )
    assert result.record.all_prerequisites_status.value == (
        "ALL_PREREQUISITES_USER_CONFIRMED"
    )


def test_identical_record_is_reported_as_already_recorded():
    source = preview_record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    registry = EvidencePlanPreparationRegistry().with_record(source)
    result = EvidencePlanPreparationPreviewService().preview(
        source.confirmation_input, plans=(ready_plan(),), registry=registry
    )
    assert result.registry_state == "ALREADY_RECORDED"
    assert registry.records == (source,)


def test_divergent_identity_is_rejected_without_mutating_registry():
    source = preview_record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    registry = EvidencePlanPreparationRegistry().with_record(source)
    before = registry
    with pytest.raises(ValueError, match="PREPARATION_CONFIRMATION_DIVERGENT"):
        EvidencePlanPreparationPreviewService().preview(
            replace(
                source.confirmation_input,
                declaration_source="CHANGED_SOURCE",
            ),
            plans=(ready_plan(),),
            registry=registry,
        )
    assert registry is before


def test_failed_plan_resolution_does_not_touch_registry():
    source = preview_record(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
    )
    registry = EvidencePlanPreparationRegistry()
    with pytest.raises(ValueError, match="PREPARATION_PLAN_UNKNOWN"):
        EvidencePlanPreparationPreviewService().preview(
            source.confirmation_input, plans=(), registry=registry
        )
    assert registry.records == ()
