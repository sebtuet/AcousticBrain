from dataclasses import asdict, fields

from acousticbrain.models import (
    EvidenceLevel,
    EvidenceReference,
    ExplanationLink,
    TraceabilityAnalysis,
)


def test_evidence_reference_identifies_a_structured_analysis_fact():
    evidence = EvidenceReference(
        code="evidence.stereo.symmetry",
        source_analysis="StereoAnalysis",
        fact_code="stereo.symmetry_score",
        evidence_level=EvidenceLevel.CALCULATED,
        value=52.5,
    )

    assert evidence.source_analysis == "StereoAnalysis"
    assert evidence.fact_code == "stereo.symmetry_score"
    assert evidence.evidence_level is EvidenceLevel.CALCULATED
    assert asdict(evidence)["value"] == 52.5


def test_explanation_link_connects_facts_to_correlations_and_actions():
    link = ExplanationLink(
        code="explanation.stereo_sbir_placement",
        fact_codes=("stereo.symmetry_score", "sbir.score"),
        evidence_codes=("evidence.stereo.symmetry", "evidence.sbir.score"),
        correlation_codes=("STEREO_SBIR_PLACEMENT_INTERACTION",),
        recommendation_codes=("TEST_SPEAKER_DISTANCE",),
    )

    assert link.fact_codes == ("stereo.symmetry_score", "sbir.score")
    assert link.correlation_codes == ("STEREO_SBIR_PLACEMENT_INTERACTION",)
    assert link.recommendation_codes == ("TEST_SPEAKER_DISTANCE",)


def test_traceability_analysis_defaults_to_an_explicit_empty_graph():
    analysis = TraceabilityAnalysis()

    assert analysis.evidence_references == []
    assert analysis.links == []
    assert analysis.source_analyses == ()


def test_traceability_contract_contains_no_rendering_or_diagnostic_text():
    field_names = set()
    for model in (EvidenceReference, ExplanationLink, TraceabilityAnalysis):
        field_names.update(field.name for field in fields(model))

    assert field_names.isdisjoint(
        {"diagnostic", "diagnostics", "title", "message", "description"}
    )
