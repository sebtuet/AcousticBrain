import pytest

from acousticbrain.report.campaign_user_assessment_human_text import (
    CampaignUserAssessmentHumanText,
)


@pytest.mark.parametrize(
    "state",
    (
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "CONTRADICTED",
        "INSUFFICIENT_EVIDENCE",
        "CONTRADICTORY_EVIDENCE",
        "NON_DISCRIMINATED",
        "NO_APPLICABLE_RULE",
    ),
)
def test_every_v1_reasoning_conclusion_has_closed_human_text(state):
    text = CampaignUserAssessmentHumanText.conclusion(state)

    assert text != state
    assert "No human-readable meaning" not in text


@pytest.mark.parametrize(
    "state",
    (
        "APPLICABLE",
        "CONDITIONALLY_APPLICABLE",
        "BLOCKED_BY_CONTRADICTION",
        "BLOCKED_BY_MISSING_PARAMETERS",
        "BLOCKED_BY_HISTORY",
        "ALREADY_TESTED",
        "NOT_SUPPORTED",
        "NO_ACTION_REQUIRED",
    ),
)
def test_every_v1_action_applicability_has_closed_human_text(state):
    text = CampaignUserAssessmentHumanText.action_applicability(state)

    assert text != state
    assert "No human-readable meaning" not in text


def test_ready_and_unverified_prerequisites_remain_qualified():
    ready = CampaignUserAssessmentHumanText.plan_status("READY")
    prerequisites = CampaignUserAssessmentHumanText.prerequisite_status(
        "AVAILABILITY_NOT_VERIFIED"
    )

    assert "planning state" in ready
    assert "does not mean the experiment is ready to execute" in ready
    assert prerequisites == "These prerequisites still need to be confirmed."


@pytest.mark.parametrize(
    "forbidden",
    ("proven cause", "optimal", "best treatment", "safe to move", "will improve"),
)
def test_closed_human_vocabulary_contains_no_forbidden_claim(forbidden):
    rendered = " ".join(
        (
            *CampaignUserAssessmentHumanText.CONCLUSIONS.values(),
            *CampaignUserAssessmentHumanText.ACTION_APPLICABILITY.values(),
            *CampaignUserAssessmentHumanText.PLAN_STATUSES.values(),
            *CampaignUserAssessmentHumanText.PREREQUISITE_STATUSES.values(),
        )
    ).casefold()

    assert forbidden not in rendered
