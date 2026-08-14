import pytest

from acousticbrain.application import (
    ChannelIsolationDocumentationReviewService,
    ChannelIsolationOperationalWorksheetService,
)
from test_evidence_plan_preparation_resolution import confirmation, ready_plan


def complete_records(plan):
    generated = ChannelIsolationOperationalWorksheetService().generate(
        plan.plan_id, plans=(plan,)
    )
    microphone = dict(generated.microphone_position)
    settings = dict(generated.acquisition_settings)
    microphone.update(
        reference_geometry="Room centerline and front wall.",
        position_description="Documented listening point.",
        orientation_description="Vertical capsule orientation.",
    )
    settings.update(
        gain="Recorded interface gain.",
        time_window="Recorded REW time window.",
        signal_chain="Recorded source and interface routing.",
        reuse_declaration="INTENDED_UNCHANGED",
    )
    return microphone, settings


def test_review_maps_complete_records_without_deciding_preparation_statuses():
    plan = ready_plan()
    microphone, settings = complete_records(plan)
    source = confirmation(plan)
    result = ChannelIsolationDocumentationReviewService().review(
        plan.plan_id, microphone, settings, source, plans=(plan,)
    )
    assert tuple(row.prerequisite_code for row in result.rows) == (
        "documented_microphone_position",
        "existing_acquisition_settings",
    )
    assert all(row.documentation_state == "DOCUMENTATION_AVAILABLE" for row in result.rows)
    assert all(row.decision_state == "USER_PREPARATION_DECISION_REQUIRED" for row in result.rows)
    assert result.source_confirmation_id == source.confirmation_id
    assert result.user_action_state == "EXPLICIT_PREPARATION_REVISION_REQUIRED"
    assert source == confirmation(plan)


def test_review_rejects_incomplete_documentation_before_mapping():
    plan = ready_plan()
    generated = ChannelIsolationOperationalWorksheetService().generate(
        plan.plan_id, plans=(plan,)
    )
    with pytest.raises(ValueError, match="DOCUMENTATION_INCOMPLETE"):
        ChannelIsolationDocumentationReviewService().review(
            plan.plan_id,
            generated.microphone_position,
            generated.acquisition_settings,
            confirmation(plan),
            plans=(plan,),
        )


def test_review_rejects_source_from_another_plan():
    plan = ready_plan()
    microphone, settings = complete_records(plan)
    other = ready_plan(plan_id="OTHER_READY_PLAN")
    with pytest.raises(ValueError, match="source plan identity"):
        ChannelIsolationDocumentationReviewService().review(
            plan.plan_id,
            microphone,
            settings,
            confirmation(other),
            plans=(plan, other),
        )
