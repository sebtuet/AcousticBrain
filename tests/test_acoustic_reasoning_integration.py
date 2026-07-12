from types import SimpleNamespace

from acousticbrain.analysis import RecommendationEngine, TraceabilityEngine
from acousticbrain.diagnostics import AcousticReasoningDiagnostic
from acousticbrain.models import (
    AcousticHypothesis,
    AcousticReasoningAnalysis,
    EvidenceRole,
    HypothesisCode,
    HypothesisStatus,
    ReasoningEvidence,
    RecommendationPriority,
    VerificationAction,
    VerificationActionType,
)


def reasoning_analysis(status=HypothesisStatus.PLAUSIBLE):
    evidence = ReasoningEvidence(
        code="reasoning.sbir_placement_interaction.match",
        role=EvidenceRole.SUPPORTING,
        fact_code="sbir.best_match_score",
        source_analysis="SBIRAnalysis",
        value=80.0,
        strength=80.0,
        confidence=90.0,
        threshold_codes=("SBIR_MATCH_AVAILABLE",),
    )
    action = VerificationAction(
        code="VERIFY_SBIR_PLACEMENT",
        action_type=VerificationActionType.TEMPORARY_MOVE,
        target="speaker_distance_to_candidate_surface",
        priority=RecommendationPriority.MEDIUM,
        confidence=90.0,
        evidence_fact_codes=(evidence.fact_code,),
        expected_supporting_fact_codes=("verification.frequency_moves",),
        expected_counter_fact_codes=("verification.frequency_unchanged",),
    )
    hypothesis = AcousticHypothesis(
        code=HypothesisCode.SBIR_PLACEMENT_INTERACTION,
        phenomenon="sbir_placement",
        domain_codes=("SBIR",),
        supporting_evidence=(evidence,),
        counter_evidence=(),
        context_evidence=(),
        missing_facts=(),
        applied_rule_codes=("SBIR_BEST_MATCH_SUPPORT",),
        support_score=80.0,
        confidence=90.0,
        status=status,
        verification_actions=(action,),
    )
    return AcousticReasoningAnalysis(
        hypotheses=(hypothesis,),
        source_analyses=("SBIRAnalysis",),
        confidence=90.0,
    )


def test_reasoning_actions_enter_recommendations_only_as_verification():
    result = RecommendationEngine().analyze(
        acoustic_reasoning=reasoning_analysis(HypothesisStatus.INCONCLUSIVE)
    )

    recommendation = result.recommendations[0]
    assert recommendation.code == "VERIFY_SBIR_PLACEMENT"
    assert recommendation.verification_action is True
    assert recommendation.hypothesis_codes == ("SBIR_PLACEMENT_INTERACTION",)
    assert recommendation.parameters["support_score"] == 80.0


def test_traceability_builds_complete_fact_hypothesis_action_chain():
    reasoning = reasoning_analysis()
    recommendations = RecommendationEngine().analyze(
        acoustic_reasoning=reasoning
    )
    result = TraceabilityEngine().analyze(
        global_analysis=SimpleNamespace(
            domains=[], correlations=[], source_analyses=()
        ),
        recommendation_analysis=recommendations,
        acoustic_reasoning=reasoning,
    )

    hypothesis_link = next(item for item in result.links if item.hypothesis_codes)
    action_link = next(item for item in result.links if item.action_codes)
    assert hypothesis_link.fact_codes == ("sbir.best_match_score",)
    assert action_link.evidence_codes == hypothesis_link.evidence_codes
    assert action_link.recommendation_codes == ("VERIFY_SBIR_PLACEMENT",)


def test_reasoning_diagnostic_only_restates_structured_decisions():
    diagnostic = AcousticReasoningDiagnostic().analyze(
        SimpleNamespace(acoustic_reasoning_analysis=reasoning_analysis())
    )

    assert diagnostic.score is None
    assert "SBIR_PLACEMENT_INTERACTION" in diagnostic.observations[0]
    assert diagnostic.causes == []
    assert diagnostic.recommendations == [
        "VERIFY_SBIR_PLACEMENT — speaker_distance_to_candidate_surface."
    ]
