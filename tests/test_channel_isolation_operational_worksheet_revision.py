import pytest

from acousticbrain.application import (
    ChannelIsolationOperationalWorksheetRevisionService,
    ChannelIsolationOperationalWorksheetService,
)
from test_evidence_plan_preparation_resolution import ready_plan


def worksheets():
    plan = ready_plan()
    generated = ChannelIsolationOperationalWorksheetService().generate(
        plan.plan_id, plans=(plan,)
    )
    return plan, generated.microphone_position, generated.acquisition_settings


def complete_assignments():
    return {
        "microphone_position.reference_geometry": "Explicit documented geometry.",
        "microphone_position.position_description": "Explicit microphone position.",
        "microphone_position.orientation_description": "Explicit microphone orientation.",
        "acquisition_settings.gain": "Explicit recorded gain.",
        "acquisition_settings.time_window": "Explicit recorded time window.",
        "acquisition_settings.signal_chain": "Explicit recorded signal chain.",
        "acquisition_settings.reuse_declaration": "INTENDED_UNCHANGED",
    }


def test_partial_revision_preserves_sources_and_remaining_markers():
    plan, microphone, settings = worksheets()
    microphone_before = dict(microphone)
    settings_before = dict(settings)
    result = ChannelIsolationOperationalWorksheetRevisionService().revise(
        plan.plan_id,
        microphone,
        settings,
        {"microphone_position.reference_geometry": "Front wall centerline reference."},
        plans=(plan,),
    )
    assert result.documentation_status == "DOCUMENTATION_INCOMPLETE"
    assert result.changed_fields == ("microphone_position.reference_geometry",)
    assert "microphone_position.reference_geometry" not in result.missing_fields
    assert "acquisition_settings.gain" in result.missing_fields
    assert microphone == microphone_before
    assert settings == settings_before
    assert result.microphone_position["record_id"] == microphone["record_id"]


def test_complete_revision_passes_both_strict_record_loaders():
    plan, microphone, settings = worksheets()
    result = ChannelIsolationOperationalWorksheetRevisionService().revise(
        plan.plan_id,
        microphone,
        settings,
        complete_assignments(),
        plans=(plan,),
    )
    assert result.documentation_status == "DOCUMENTATION_COMPLETE"
    assert result.missing_fields == ()
    assert result.acquisition_settings["reuse_declaration"] == "INTENDED_UNCHANGED"


@pytest.mark.parametrize(
    ("assignments", "message"),
    (
        ({}, "At least one"),
        ({"unknown.field": "value"}, "Unknown operational assignment"),
        ({"acquisition_settings.gain": " value "}, "exact non-empty"),
        (
            {"acquisition_settings.reuse_declaration": "MAYBE"},
            "Invalid reuse declaration",
        ),
        (
            {"acquisition_settings.gain": "REPLACE_WITH_SOMETHING"},
            "cannot restore placeholders",
        ),
    ),
)
def test_invalid_assignments_are_rejected(assignments, message):
    plan, microphone, settings = worksheets()
    with pytest.raises(ValueError, match=message):
        ChannelIsolationOperationalWorksheetRevisionService().revise(
            plan.plan_id,
            microphone,
            settings,
            assignments,
            plans=(plan,),
        )


def test_invalid_partially_filled_source_is_rejected_before_revision():
    plan, microphone, settings = worksheets()
    microphone["position_description"] = " invalid surrounding whitespace "
    with pytest.raises(ValueError, match="exact non-empty"):
        ChannelIsolationOperationalWorksheetRevisionService().revise(
            plan.plan_id,
            microphone,
            settings,
            {"acquisition_settings.gain": "Explicit gain."},
            plans=(plan,),
        )


def test_guidance_covers_every_closed_assignment_path_without_answers():
    service = ChannelIsolationOperationalWorksheetRevisionService()
    paths = tuple(value.path for value in service.GUIDANCE)
    assert set(paths) == service.ALLOWED_PATHS
    assert len(paths) == len(set(paths))
    reuse = next(
        value for value in service.GUIDANCE
        if value.path == "acquisition_settings.reuse_declaration"
    )
    assert reuse.allowed_values == (
        "INTENDED_UNCHANGED",
        "NOT_INTENDED_UNCHANGED",
    )
    assert all(value.question and value.limitation for value in service.GUIDANCE)
