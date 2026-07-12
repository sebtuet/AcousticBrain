from dataclasses import FrozenInstanceError

import pytest

from acousticbrain.models import (
    AcousticHypothesis,
    AcousticReasoningAnalysis,
    EvidenceRole,
    HypothesisCode,
    HypothesisStatus,
    MissingReasoningFact,
    ReasoningEvidence,
    RecommendationPriority,
    VerificationAction,
    VerificationActionType,
)


def evidence(role=EvidenceRole.SUPPORTING, code="evidence.test"):
    return ReasoningEvidence(
        code=code,
        role=role,
        fact_code="test.fact",
        source_analysis="TestAnalysis",
        value=1.0,
        strength=80.0,
        confidence=90.0,
        threshold_codes=("TEST_THRESHOLD",),
    )


def action(*, definitive=False):
    return VerificationAction(
        code="VERIFY_TEST",
        action_type=VerificationActionType.MEASURE,
        target="test_target",
        priority=RecommendationPriority.MEDIUM,
        confidence=80.0,
        evidence_fact_codes=("test.fact",),
        expected_supporting_fact_codes=("test.after.support",),
        expected_counter_fact_codes=("test.after.counter",),
        parameters={"repeat_count": 1},
        definitive=definitive,
    )


def hypothesis(status=HypothesisStatus.PLAUSIBLE, actions=None):
    return AcousticHypothesis(
        code=HypothesisCode.SBIR_PLACEMENT_INTERACTION,
        phenomenon="sbir_placement",
        domain_codes=("SBIR",),
        supporting_evidence=(evidence(),),
        counter_evidence=(),
        context_evidence=(),
        missing_facts=(
            MissingReasoningFact(
                fact_code="geometry.speaker_position",
                source_analysis="RoomGeometry",
                rule_code="SBIR_REQUIRE_GEOMETRY",
            ),
        ),
        applied_rule_codes=("SBIR_SUPPORT_MATCH",),
        support_score=80.0,
        confidence=75.0,
        status=status,
        verification_actions=(action(),) if actions is None else actions,
    )


def test_reasoning_contract_separates_support_confidence_and_missing_facts():
    result = hypothesis()

    assert result.support_score == 80.0
    assert result.confidence == 75.0
    assert result.supporting_evidence[0].role is EvidenceRole.SUPPORTING
    assert result.counter_evidence == ()
    assert result.missing_facts[0].fact_code == "geometry.speaker_position"


def test_reasoning_models_and_action_parameters_are_immutable():
    result = hypothesis()

    with pytest.raises(FrozenInstanceError):
        result.support_score = 1.0
    with pytest.raises(TypeError):
        result.verification_actions[0].parameters["repeat_count"] = 2


def test_inconclusive_hypothesis_rejects_definitive_correction():
    with pytest.raises(ValueError, match="Inconclusive"):
        hypothesis(
            status=HypothesisStatus.INCONCLUSIVE,
            actions=(action(definitive=True),),
        )


def test_action_requires_a_complete_evidence_chain():
    with pytest.raises(ValueError, match="provenance"):
        VerificationAction(
            code="INVALID",
            action_type=VerificationActionType.MEASURE,
            target="test",
            priority=RecommendationPriority.LOW,
            confidence=50.0,
            evidence_fact_codes=(),
            expected_supporting_fact_codes=("after",),
            expected_counter_fact_codes=("counter",),
        )


def test_hypothesis_rejects_action_referencing_an_unknown_fact():
    invalid_action = VerificationAction(
        code="INVALID",
        action_type=VerificationActionType.MEASURE,
        target="test",
        priority=RecommendationPriority.LOW,
        confidence=50.0,
        evidence_fact_codes=("unknown.fact",),
        expected_supporting_fact_codes=("after",),
        expected_counter_fact_codes=("counter",),
    )

    with pytest.raises(ValueError, match="hypothesis evidence"):
        hypothesis(actions=(invalid_action,))


def test_reasoning_analysis_rejects_duplicate_hypotheses():
    with pytest.raises(ValueError, match="unique"):
        AcousticReasoningAnalysis(
            hypotheses=(hypothesis(), hypothesis()),
            source_analyses=("TestAnalysis",),
            confidence=75.0,
        )
