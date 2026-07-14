from acousticbrain.commands.demo_guided_room_description import run_demo


def test_confirmed_demo_exercises_the_complete_guided_workflow_in_memory():
    result = run_demo("confirmed")

    assert result["isolation"] == {
        "mode": "IN_MEMORY_SYNTHETIC_PROJECT",
        "reads_measurements_directory": False,
        "writes_project_files": False,
    }
    assert result["proposal_before_confirmation"]["status"] == (
        "READY_FOR_CONFIRMATION"
    )
    assert result["before_confirmation"]["persisted_json_unchanged"]
    assert not result["before_confirmation"]["analysis_rerun_triggered"]
    assert result["confirmation"] == {
        "status": "CONFIRMED",
        "persisted": False,
    }
    assert result["application"]["status"] == "APPLIED"
    assert result["application"]["full_analysis_triggered"]
    assert result["application"]["full_analysis_call_count"] == 1


def test_confirmed_demo_preserves_distinct_description_and_profile_provenance():
    assignment = run_demo("confirmed")["application"]["material_assignment"]

    assert assignment["description_source"] == "USER_DESCRIPTION_INTERPRETED"
    assert assignment["description_provenance"] == [
        "USER_DESCRIPTION_INTERPRETED"
    ]
    assert assignment["catalog_entry_id"] == (
        "material.gypsum_board_painted.v1"
    )
    assert assignment["catalog_entry_version_is_explicit"]
    assert assignment["profile_source"] == "CATALOG_ESTIMATE"
    assert assignment["profile_confidence"] == 65.0
    assert assignment["profile_provenance"] == [
        "INTERNAL_VERSIONED_MATERIAL_CATALOG"
    ]


def test_demo_never_presents_projected_capabilities_as_eligibility():
    projection = run_demo("confirmed")["proposal_before_confirmation"]

    assert projection["potentially_unblocked_capabilities"]
    assert not projection["capability_projection_is_eligibility"]
    assert "complete new analysis" in projection["eligibility_disclaimer"]


def test_ambiguous_demo_requires_clarification_without_writing_or_analysis():
    result = run_demo("ambiguous")

    assert result["interpretation"]["status"] == "AMBIGUOUS"
    assert result["interpretation"]["candidate_value_ids"] == []
    assert result["interpretation"]["ambiguity_codes"] == [
        "MATERIAL_DESCRIPTION_AMBIGUOUS"
    ]
    assert result["proposal_before_confirmation"]["status"] == (
        "NEEDS_CLARIFICATION"
    )
    assert result["before_confirmation"]["persisted_json_unchanged"]
    assert result["confirmation"] is None
    assert result["application"] is None
