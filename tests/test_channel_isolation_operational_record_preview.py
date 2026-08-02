from acousticbrain.application import (
    ChannelIsolationOperationalRecordPreviewService,
    ChannelIsolationOperationalWorksheetService,
)
from test_evidence_plan_preparation_resolution import ready_plan


def worksheets():
    plan = ready_plan()
    result = ChannelIsolationOperationalWorksheetService().generate(
        plan.plan_id, plans=(plan,)
    )
    return plan, result.microphone_position, result.acquisition_settings


def test_placeholder_worksheets_are_incomplete_with_exact_fields():
    plan, microphone, settings = worksheets()
    result = ChannelIsolationOperationalRecordPreviewService().preview(
        plan.plan_id, microphone, settings, plans=(plan,)
    )
    assert result.status == "DOCUMENTATION_INCOMPLETE"
    assert result.user_action_state == "COMPLETE_OPERATIONAL_DOCUMENTATION"
    assert result.missing_fields == (
        "acquisition_settings.gain",
        "acquisition_settings.reuse_declaration",
        "acquisition_settings.signal_chain",
        "acquisition_settings.time_window",
        "microphone_position.orientation_description",
        "microphone_position.position_description",
        "microphone_position.reference_geometry",
    )


def test_completed_documentation_is_loaded_strictly_without_confirming_preparation():
    plan, microphone, settings = worksheets()
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
    result = ChannelIsolationOperationalRecordPreviewService().preview(
        plan.plan_id, microphone, settings, plans=(plan,)
    )
    assert result.status == "DOCUMENTATION_COMPLETE"
    assert result.user_action_state == "REVIEW_PREPARATION_STATUS_SEPARATELY"
    assert result.missing_fields == ()
