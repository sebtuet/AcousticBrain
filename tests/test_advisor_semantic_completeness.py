from dataclasses import replace
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.advisor import AdvisorContextBuilder, AdvisorService, MockAdvisorProvider
from acousticbrain.models import (
    AdvisorAudience,
    AdvisorDetailLevel,
    AdvisorDimensionStatus,
    AdvisorResponseLanguage,
    AdvisorResponseSource,
    AdvisorValidationStatus,
)
from tests.test_optional_llm_advisor import Item, deterministic_report


def report_with_plans():
    report = deterministic_report()
    common = {
        "source_reasoning_id": "REASONING_A",
        "blocking_factor_id": "blocking.action_a.missing",
        "objective": "Acquire deterministic evidence",
        "required_inputs": (),
        "expected_outputs": (),
        "limitations": ("The plan changes no upstream object.",),
    }
    ready = Item(plan_id="PLAN_READY", status="READY", **common)
    blocked = Item(
        plan_id="PLAN_BLOCKED",
        status="BLOCKED",
        missing_parameters=("protocol_id",),
        **common,
    )
    report.evidence_acquisition_plans = SimpleNamespace(plans=(ready, blocked))
    return report


def advise_with(provider, *, language=AdvisorResponseLanguage.EN, report=None):
    return AdvisorService().advise(
        report or report_with_plans(),
        question="Explain the problems, blocking factors and plans.",
        audience=AdvisorAudience.GENERAL,
        detail_level=AdvisorDetailLevel.STANDARD,
        provider=provider,
        expected_response_language=language,
    )


class MutatingProvider(MockAdvisorProvider):
    def __init__(self, mutation):
        super().__init__()
        self.mutation = mutation

    def generate(self, request, context_projection):
        output = super().generate(request, context_projection)
        return self.mutation(output, request)


def test_context_declares_language_allowed_ids_labels_and_exact_plan_classes():
    context = AdvisorContextBuilder().build(
        report_with_plans(), expected_response_language=AdvisorResponseLanguage.FR
    )

    assert context.expected_response_language is AdvisorResponseLanguage.FR
    assert context.required_reasoning_ids == ("REASONING_A",)
    assert context.required_blocking_factor_ids == ("blocking.action_a.missing",)
    assert context.required_ready_plan_ids == ("PLAN_READY",)
    assert context.required_blocked_plan_ids == ("PLAN_BLOCKED",)
    assert context.allowed_object_ids == tuple(value.object_id for value in context.objects)
    assert dict(context.object_labels)["PLAN_READY"] == "Acquire deterministic evidence"


def test_context_rejects_an_unknown_plan_status_instead_of_classifying_it():
    report = report_with_plans()
    invalid = Item(**{
        **report.evidence_acquisition_plans.plans[0].__dict__,
        "status": "PENDING",
    })
    report.evidence_acquisition_plans = SimpleNamespace(plans=(invalid,))

    with pytest.raises(ValueError, match="Advisor plan status is invalid"):
        AdvisorContextBuilder().build(report)


def test_compliant_mock_is_valid_in_french_and_covers_every_category():
    response = advise_with(MockAdvisorProvider(), language=AdvisorResponseLanguage.FR)

    assert response.validation_status is AdvisorValidationStatus.VALID
    assert response.response_source is AdvisorResponseSource.PROVIDER
    assert response.response_language is AdvisorResponseLanguage.FR
    assert response.covered_reasoning_ids == ("REASONING_A",)
    assert response.covered_blocking_factor_ids == ("blocking.action_a.missing",)
    assert response.covered_ready_plan_ids == ("PLAN_READY",)
    assert response.covered_blocked_plan_ids == ("PLAN_BLOCKED",)
    assert "Résumé des problèmes" in response.answer_text
    assert "READY" in response.answer_text and "BLOCKED" in response.answer_text


@pytest.mark.parametrize(
    ("field", "status", "violation"),
    (
        ("covered_reasoning_ids", "semantic_coverage_status", "MISSING_REASONING_COVERAGE"),
        ("covered_blocking_factor_ids", "semantic_coverage_status", "MISSING_BLOCKING_FACTOR_COVERAGE"),
        ("covered_ready_plan_ids", "semantic_coverage_status", "MISSING_READY_PLAN_COVERAGE"),
        ("covered_blocked_plan_ids", "semantic_coverage_status", "MISSING_BLOCKED_PLAN_COVERAGE"),
    ),
)
def test_missing_structured_coverage_is_rejected(field, status, violation):
    response = advise_with(MutatingProvider(lambda output, _: replace(output, **{field: ()})))

    assert response.validation_status is AdvisorValidationStatus.INVALID
    assert response.response_source is AdvisorResponseSource.LOCAL_SAFETY_RESPONSE
    assert getattr(response, status) is AdvisorDimensionStatus.INVALID
    assert any(value.startswith(violation) for value in response.unsupported_claims)


def test_duplicate_unknown_reordered_and_cross_classified_plan_coverage_are_rejected():
    mutations = (
        lambda output, _: replace(output, covered_ready_plan_ids=("PLAN_READY", "PLAN_READY")),
        lambda output, _: replace(output, covered_ready_plan_ids=("UNKNOWN_PLAN",)),
        lambda output, _: replace(
            output,
            covered_ready_plan_ids=("PLAN_READY", "PLAN_BLOCKED"),
            covered_blocked_plan_ids=("PLAN_BLOCKED",),
        ),
    )
    for mutation in mutations:
        response = advise_with(MutatingProvider(mutation))
        assert response.semantic_coverage_status is AdvisorDimensionStatus.INVALID
        assert response.response_source is AdvisorResponseSource.LOCAL_SAFETY_RESPONSE


@pytest.mark.parametrize(
    "answer",
    (
        "The answer restates only the supplied deterministic objects.",
        "Generic answer with no useful synthesis.",
        "The plan changes no upstream object.",
        "Problem summary and blocking factors are preserved, but no plan is discussed at all despite the supplied context.",
    ),
)
def test_degenerate_answers_are_rejected(answer):
    response = advise_with(MutatingProvider(lambda output, _: replace(output, answer=answer)))

    assert response.degeneracy_status is AdvisorDimensionStatus.INVALID
    assert response.response_source is AdvisorResponseSource.LOCAL_SAFETY_RESPONSE


def test_declared_language_and_manifest_text_language_are_validated_separately():
    declared = advise_with(MutatingProvider(
        lambda output, _: replace(output, response_language=AdvisorResponseLanguage.FR)
    ))
    french_text_declared_english = advise_with(MutatingProvider(
        lambda output, _: replace(
            output,
            answer=(
                "Résumé des problèmes déterministes avec les blocages préservés. "
                "Plans READY prêts : PLAN_READY. Plans BLOCKED bloqués : PLAN_BLOCKED. "
                "Aucune action bloquée n’est présentée comme applicable."
            ),
        )
    ))

    assert declared.response_language_status is AdvisorDimensionStatus.INVALID
    assert french_text_declared_english.response_language_status is AdvisorDimensionStatus.INVALID


def test_invalid_provider_gets_deterministic_structured_safety_answer_in_requested_language():
    provider = MutatingProvider(lambda output, _: replace(output, covered_ready_plan_ids=()))
    first = advise_with(provider, language=AdvisorResponseLanguage.FR)
    second = advise_with(provider, language=AdvisorResponseLanguage.FR)

    assert first == second
    assert first.response_source is AdvisorResponseSource.LOCAL_SAFETY_RESPONSE
    assert first.answer_text.startswith("Réponse locale de sûreté")
    assert "PLAN_READY" in first.answer_text and "PLAN_BLOCKED" in first.answer_text
    assert first.covered_ready_plan_ids == ("PLAN_READY",)
    assert first.covered_blocked_plan_ids == ("PLAN_BLOCKED",)


def test_language_auto_detection_is_deterministic_and_explicit_choice_wins():
    assert acousticbrain_main.resolve_advisor_language("auto", "Résume les problèmes") is AdvisorResponseLanguage.FR
    assert acousticbrain_main.resolve_advisor_language("auto", "Summarize the problems") is AdvisorResponseLanguage.EN
    assert acousticbrain_main.resolve_advisor_language("en", "Résume les problèmes") is AdvisorResponseLanguage.EN
