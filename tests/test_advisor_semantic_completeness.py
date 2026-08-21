from dataclasses import replace

import pytest

import main as acousticbrain_main
from acousticbrain.advisor import AdvisorContextBuilder, AdvisorService, MockAdvisorProvider
from acousticbrain.models import AdvisorAudience, AdvisorDetailLevel, AdvisorDimensionStatus, AdvisorResponseLanguage, AdvisorResponseSource, AdvisorValidationStatus
from acousticbrain.report import CampaignAssessmentNextStep, CampaignAssessmentSource
from tests.test_optional_llm_advisor import deterministic_report


def report_with_plan():
    report = deterministic_report()
    step = CampaignAssessmentNextStep(
        plan_id="PLAN_READY", objective="Acquire deterministic evidence",
        test_type="CHANNEL_ISOLATION", planning_status="READY",
        selection_rationale="Selected by V1.", required_inputs=("documented_microphone_position",),
        procedure=("Acquire separate channels.",), controlled_variables=("gain",),
        variables_under_test=("active_channel",), measurements=("response",),
        prerequisite_status="AVAILABILITY_NOT_VERIFIED", limitations=("Not executed.",),
        priority="CRITICAL", estimated_effort="MEDIUM",
        provenance=(CampaignAssessmentSource("EVIDENCE_PLAN", "PLAN_READY"),),
    )
    report.campaign_user_assessment = replace(
        report.campaign_user_assessment,
        recommended_next_step=step, prerequisites=step.required_inputs,
        scientific_boundaries=(
            *report.campaign_user_assessment.scientific_boundaries,
            "READY does not establish execution readiness.",
            "APPLICABLE does not establish benefit or physical safety.",
        ),
    )
    return report


def advise_with(provider, *, question="What should I do next?", language=AdvisorResponseLanguage.EN):
    return AdvisorService().advise(
        report_with_plan(), question=question, audience=AdvisorAudience.GENERAL,
        detail_level=AdvisorDetailLevel.STANDARD, provider=provider,
        expected_response_language=language,
    )


class MutatingProvider(MockAdvisorProvider):
    def __init__(self, answer):
        super().__init__()
        self.answer = answer

    def generate(self, request, context_projection):
        return replace(super().generate(request, context_projection), answer=self.answer)


def test_context_declares_language_sources_and_exact_selected_plan():
    context = AdvisorContextBuilder().build(
        report_with_plan(), expected_response_language=AdvisorResponseLanguage.FR
    )
    assert context.schema_version == "advisor-assessment-context.v1"
    assert context.required_ready_plan_ids == ("PLAN_READY",)
    assert context.required_blocked_plan_ids == ()
    assert "PLAN_READY" in context.allowed_source_ids
    assert all(value.object_type != "EVIDENCE_WEIGHT" for value in context.objects)


@pytest.mark.parametrize("answer", (
    "The SUPPORTED finding is an established cause in this room.",
    "The planning contract is READY, so it is ready to run immediately.",
    "The APPLICABLE action will improve the result.",
    "The prerequisite available state is confirmed.",
    "The main problem is the asymmetric response.",
    "The best treatment is absorption at the first reflection point.",
    "The optimal placement is 40 cm forward.",
))
def test_semantic_overreach_is_rejected_locally(answer):
    response = advise_with(MutatingProvider(answer))
    assert response.validation_status is AdvisorValidationStatus.INVALID
    assert response.scientific_fidelity_status is AdvisorDimensionStatus.INVALID
    assert response.response_source is AdvisorResponseSource.LOCAL_SAFETY_RESPONSE
    assert any(value.startswith("BOUNDED_SEMANTIC_OVERREACH") for value in response.unsupported_claims)


def test_safety_response_describes_ready_as_planning_not_execution():
    response = advise_with(MutatingProvider("The plan is ready to execute now."))
    assert "READY planning contracts" in response.answer_text
    assert "executability not established" in response.answer_text
    assert "ready to run" not in response.answer_text.casefold()


def test_language_auto_detection_is_deterministic_and_explicit_choice_wins():
    assert acousticbrain_main.resolve_advisor_language("auto", "Résume les problèmes") is AdvisorResponseLanguage.FR
    assert acousticbrain_main.resolve_advisor_language("auto", "Summarize the problems") is AdvisorResponseLanguage.EN
    assert acousticbrain_main.resolve_advisor_language("en", "Résume les problèmes") is AdvisorResponseLanguage.EN
