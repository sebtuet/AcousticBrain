from acousticbrain.knowledge_codes import (
    FactCode,
    GlobalCorrelationCode,
    GlobalDomainCode,
    RecommendationCode,
    SourceAnalysisCode,
)
from acousticbrain.models import (
    EvidenceLevel,
    EvidenceReference,
    ExplanationLink,
    GlobalDomainAnalysis,
    Recommendation,
    RecommendationPriority,
    TraceabilityAnalysis,
)
from acousticbrain.report import TraceabilityPresenter


def test_existing_global_contract_represents_all_new_domains():
    domains = [
        GlobalDomainAnalysis(
            code=domain,
            score=score,
            confidence=confidence,
            source_analysis=source,
            recommendation_codes=(recommendation,),
        )
        for domain, source, recommendation, score, confidence in (
            (
                GlobalDomainCode.RT60,
                SourceAnalysisCode.RT60,
                RecommendationCode.INVESTIGATE_RT60_CHANNEL_DIFFERENCES,
                60.0,
                94.0,
            ),
            (
                GlobalDomainCode.ETC,
                SourceAnalysisCode.ETC,
                RecommendationCode.TREAT_DOMINANT_EARLY_REFLECTIONS,
                40.0,
                91.0,
            ),
            (
                GlobalDomainCode.CLARITY,
                SourceAnalysisCode.CLARITY,
                RecommendationCode.CHECK_EARLY_REFLECTION_SYMMETRY,
                70.0,
                91.0,
            ),
            (
                GlobalDomainCode.SPATIAL,
                SourceAnalysisCode.SPATIAL,
                RecommendationCode.VERIFY_TIME_ALIGNMENT,
                50.0,
                67.0,
            ),
        )
    ]

    assert [domain.code for domain in domains] == [
        "RT60",
        "ETC",
        "CLARITY",
        "SPATIAL",
    ]
    assert all(domain.source_analysis.endswith("Analysis") for domain in domains)


def test_existing_recommendation_contract_preserves_multiple_sources():
    recommendation = Recommendation(
        code=RecommendationCode.CHECK_EARLY_REFLECTION_SYMMETRY,
        action="check_symmetry",
        target="early_reflections",
        priority=RecommendationPriority.HIGH,
        confidence=85.0,
        source_analyses=(
            SourceAnalysisCode.ETC,
            SourceAnalysisCode.SPATIAL,
        ),
    )

    assert recommendation.source_analyses == (
        "ETCAnalysis",
        "SpatialAnalysis",
    )


def test_incomplete_traceability_link_stays_incomplete_in_presentation():
    missing_evidence_code = "evidence.spatial.missing"
    link = ExplanationLink(
        code="explanation.recommendation.verify_time_alignment",
        fact_codes=(FactCode.SPATIAL_TECHNICAL_CENTER_STABILITY,),
        evidence_codes=(missing_evidence_code,),
        correlation_codes=(GlobalCorrelationCode.SPATIAL_STEREO_ALIGNMENT,),
        recommendation_codes=(RecommendationCode.VERIFY_TIME_ALIGNMENT,),
    )
    analysis = TraceabilityAnalysis(links=[link])
    context = type("Context", (), {"traceability_analysis": analysis})()

    presented = TraceabilityPresenter().present(context)

    assert presented.evidence_references == []
    assert presented.links[0].evidence_codes == (missing_evidence_code,)
    assert presented.links[0].recommendation_codes == (
        RecommendationCode.VERIFY_TIME_ALIGNMENT,
    )


def test_evidence_contract_keeps_atomic_new_domain_fact():
    evidence = EvidenceReference(
        code="evidence.rt60.reliable_difference_count",
        source_analysis=SourceAnalysisCode.RT60,
        fact_code=FactCode.RT60_RELIABLE_DIFFERENCE_COUNT,
        evidence_level=EvidenceLevel.CALCULATED,
        value=3,
    )

    assert evidence.value == 3
    assert evidence.fact_code == "rt60.reliable_difference_count"
