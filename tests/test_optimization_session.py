from pathlib import Path
from types import SimpleNamespace

import pytest

from acousticbrain.application import OptimizationSessionService
from acousticbrain.models import (
    AcousticHypothesis,
    AcousticReasoningAnalysis,
    EvidenceLevel,
    EvidenceReference,
    EvidenceRole,
    ExperimentProtocol,
    GlobalAnalysis,
    GlobalCorrelation,
    GlobalDomainAnalysis,
    HypothesisCode,
    HypothesisEvolutionResult,
    HypothesisStatus,
    ReasoningEvidence,
    TraceabilityAnalysis,
)


def structured_context(*, score, support, status=HypothesisStatus.PLAUSIBLE):
    fact = ReasoningEvidence(
        code="reasoning.test.fact",
        role=EvidenceRole.SUPPORTING,
        fact_code="test.fact",
        source_analysis="TestAnalysis",
        value=support,
        strength=support,
        confidence=90.0,
        correlation_codes=("TEST_CORRELATION",),
    )
    hypothesis = AcousticHypothesis(
        code=HypothesisCode.SBIR_PLACEMENT_INTERACTION,
        phenomenon="interaction",
        domain_codes=("SBIR",),
        supporting_evidence=(fact,),
        counter_evidence=(),
        context_evidence=(),
        missing_facts=(),
        applied_rule_codes=("TEST_RULE",),
        support_score=support,
        confidence=90.0,
        status=status,
    )
    return SimpleNamespace(
        measurement=SimpleNamespace(name=f"measurement-{score}"),
        global_analysis=GlobalAnalysis(
            score=score,
            domains=[
                GlobalDomainAnalysis(
                    code="SBIR",
                    score=score,
                    confidence=90.0,
                    source_analysis="SBIRAnalysis",
                )
            ],
            correlations=[
                GlobalCorrelation(
                    code="TEST_CORRELATION",
                    domain_codes=("SBIR",),
                    source_analyses=("SBIRAnalysis",),
                    score=80.0,
                )
            ],
        ),
        acoustic_reasoning_analysis=AcousticReasoningAnalysis(
            hypotheses=(hypothesis,),
            source_analyses=("SBIRAnalysis",),
            confidence=90.0,
        ),
        traceability_analysis=TraceabilityAnalysis(
            evidence_references=[
                EvidenceReference(
                    code="evidence.test.fact",
                    source_analysis="TestAnalysis",
                    fact_code="test.fact",
                    evidence_level=EvidenceLevel.CALCULATED,
                    value=support,
                )
            ],
        ),
    )


def protocol():
    return ExperimentProtocol(
        experiment_id="experiment-1",
        hypothesis_code="SBIR_PLACEMENT_INTERACTION",
        action_code="VERIFY_SBIR_PLACEMENT",
        label="Déplacement temporaire des enceintes",
        fact_codes=("test.fact",),
    )


def test_session_requires_explicit_context_and_iteration():
    service = OptimizationSessionService()
    context = service.create("session-1")

    service.attach_analysis(context, structured_context(score=50.0, support=40.0))

    with pytest.raises(ValueError, match="explicitly started iteration"):
        service.attach_analysis(context, structured_context(score=60.0, support=70.0))

    service.start_iteration(context, protocol())
    service.attach_analysis(context, structured_context(score=60.0, support=70.0))

    comparison = context.session.iterations[0].comparison
    assert comparison.before_state_id == "session-1:state:1"
    assert comparison.after_state_id == "session-1:state:2"
    assert comparison.global_gain == 10.0
    assert comparison.improved_facts[0].fact_code == "global.domain.sbir.score"
    assert comparison.hypothesis_evolution.result is HypothesisEvolutionResult.REINFORCED
    assert context.session.analysis.completed_experiments == 1


def test_traceability_chain_is_complete_and_uses_existing_structured_links():
    service = OptimizationSessionService()
    context = service.create("session-trace", detailed_traceability=True)
    service.attach_analysis(context, structured_context(score=50.0, support=40.0))
    service.start_iteration(context, protocol())
    service.attach_analysis(context, structured_context(score=60.0, support=70.0))

    chain = context.session.analysis.trace_chains[0]
    assert chain.measurement_name == "measurement-50.0"
    assert chain.fact_codes == ("test.fact",)
    assert chain.correlation_codes == ("TEST_CORRELATION",)
    assert chain.hypothesis_code == "SBIR_PLACEMENT_INTERACTION"
    assert chain.protocol_id == "experiment-1"
    assert chain.new_state_id == "session-trace:state:2"
    assert chain.comparison_id == "session-trace:comparison:1"
    assert chain.evolution_result == "REINFORCED"
    assert chain.progression_id == "session-trace:progression:1"


def test_session_save_and_load_are_explicit_and_lossless(tmp_path):
    service = OptimizationSessionService()
    context = service.create("persisted-session")
    service.attach_analysis(context, structured_context(score=50.0, support=40.0))
    service.start_iteration(context, protocol())
    service.attach_analysis(context, structured_context(score=60.0, support=70.0))
    path = tmp_path / "session.json"

    service.save(context, path)
    loaded = service.load(path)

    assert loaded.session.session_id == "persisted-session"
    assert loaded.session.states == context.session.states
    assert loaded.session.iterations == context.session.iterations
    assert loaded.session.analysis == context.session.analysis


def test_loading_does_not_create_a_missing_session(tmp_path):
    with pytest.raises(FileNotFoundError):
        OptimizationSessionService().load(tmp_path / "missing.json")
