from copy import deepcopy
from types import SimpleNamespace

import pytest

from acousticbrain.analysis.acoustic_hypothesis_experiment_generation import (
    AcousticHypothesisExperimentGenerator,
)
from acousticbrain.brain.stages.acoustic_hypothesis_experiment_generation import (
    AcousticHypothesisExperimentGenerationStage,
)
from acousticbrain.models import (
    AcousticHypothesis,
    AcousticReasoningAnalysis,
    CausalDiscriminationOutcome,
    EvidenceRole,
    GeneratedAcousticExperiment,
    GeneratedExperimentDifficulty,
    GeneratedExperimentReversibility,
    GeneratedExperimentType,
    GeneratedHypothesisStatus,
    HypothesisCode,
    HypothesisStatus,
    Peak,
    ReasoningEvidence,
    ReflectionCandidateGeometricStatus,
    RoomSurfaceKind,
)
from acousticbrain.report import AcousticHypothesisExperimentGenerationPresenter
from acousticbrain.brain import AcousticBrain
from test_golden_report import reference_project


def evidence(code, role=EvidenceRole.SUPPORTING, source="TestAnalysis"):
    return ReasoningEvidence(
        code=f"evidence.{code}",
        role=role,
        fact_code=code,
        source_analysis=source,
        value=1.0,
        strength=80.0,
        confidence=80.0,
    )


def hypothesis(code, *, status=HypothesisStatus.SUPPORTED, support=True, context=False):
    return AcousticHypothesis(
        code=code,
        phenomenon=code.value,
        domain_codes=("TEST",),
        supporting_evidence=(evidence(f"{code.value}.support"),) if support else (),
        counter_evidence=(),
        context_evidence=(
            (evidence(f"{code.value}.context", EvidenceRole.CONTEXT),)
            if context else ()
        ),
        missing_facts=(),
        applied_rule_codes=(f"RULE_{code.value}",),
        support_score=80.0 if support else 0.0,
        confidence=75.0,
        status=status,
    )


def context(*hypotheses, **values):
    defaults = dict(
        acoustic_reasoning_analysis=AcousticReasoningAnalysis(
            hypotheses=tuple(hypotheses),
            source_analyses=("TestAnalysis",),
            confidence=75.0,
        ),
        experiment_descriptors=(),
        experiment_comparison_analysis=None,
        causal_discrimination_analysis=None,
        sbir_geometry_correlation_analysis=None,
        material_aware_reflection_candidate_analysis=None,
        geometry_early_reflection_analysis=None,
        room_geometry=None,
        modal_density_analysis=None,
        bass_decay_analysis=None,
    )
    defaults.update(values)
    return SimpleNamespace(**defaults)


def descriptor(*modified_variables):
    return SimpleNamespace(
        declared_change_codes=(),
        experiment_declaration=SimpleNamespace(
            modified_variables=tuple(modified_variables)
        ),
    )


def modal_context(*, executed=False):
    source = hypothesis(
        HypothesisCode.MODAL_BASS_PERSISTENCE,
        status=HypothesisStatus.INCONCLUSIVE,
        support=False,
        context=True,
    )
    band = SimpleNamespace(minimum_hz=20.0, maximum_hz=50.0)
    return context(
        source,
        modal_density_analysis=SimpleNamespace(sparse_bands=[band], dense_bands=[]),
        experiment_descriptors=(descriptor("LISTENING_POSITION_MULTI_POINT"),)
        if executed else (),
    )


def reflection_context(*, executed=False, mixed=False, with_surface=True):
    source = hypothesis(HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION)
    if not with_surface:
        return context(source)
    assessment = SimpleNamespace(
        geometric_status=ReflectionCandidateGeometricStatus.ACCEPTED,
        informative_rank=1,
        candidate_id="reflection.left",
        surface_id="left_wall",
        path_id="path.left",
    )
    comparison = None
    if mixed:
        result = SimpleNamespace(
            modified_variables=("TEMPORARY_LEFT_FIRST_REFLECTION_ABSORPTION",),
            acoustic_outcome=SimpleNamespace(value="MIXED"),
        )
        comparison = SimpleNamespace(
            sequence=SimpleNamespace(local_comparisons=(result,))
        )
    return context(
        source,
        room_geometry=SimpleNamespace(
            surfaces=(SimpleNamespace(surface_id="left_wall", kind=RoomSurfaceKind.LEFT_WALL),)
        ),
        material_aware_reflection_candidate_analysis=SimpleNamespace(
            candidates=(assessment,)
        ),
        geometry_early_reflection_analysis=SimpleNamespace(
            paths=(SimpleNamespace(
                path_id="path.left", theoretical_delay_ms=5.0, uncertainty_ms=0.4
            ),)
        ),
        experiment_descriptors=(
            descriptor("TEMPORARY_LEFT_FIRST_REFLECTION_ABSORPTION"),
        ) if executed or mixed else (),
        experiment_comparison_analysis=comparison,
    )


def sbir_context(*, with_distance=True):
    source = hypothesis(HypothesisCode.SBIR_PLACEMENT_INTERACTION)
    if not with_distance:
        return context(source)
    candidate = SimpleNamespace(
        surface=SimpleNamespace(name="FRONT_WALL"),
        speaker_id="LEFT_SPEAKER",
        speaker_boundary_distance_m=0.54,
    )
    match = SimpleNamespace(candidate=candidate, observed_dip=Peak(160.0, -10.0, 1, 8.0))
    return context(
        source,
        sbir_geometry_correlation_analysis=SimpleNamespace(best_match=match),
    )


def test_no_reasoning_or_no_exploitable_data_produces_no_result():
    result = AcousticHypothesisExperimentGenerator().generate(
        SimpleNamespace(acoustic_reasoning_analysis=None)
    )
    assert result.hypotheses == ()
    assert result.ordered_experiments == ()
    assert result.recommended_candidate_id is None


def test_sbir_known_distance_generates_structured_ten_centimeter_test():
    result = AcousticHypothesisExperimentGenerator().generate(sbir_context())
    candidate = result.ordered_experiments[0]
    assert candidate.experiment_type is GeneratedExperimentType.LEFT_SPEAKER_FORWARD
    assert candidate.movement_direction == "FORWARD_AWAY_FROM_FRONT_WALL"
    assert candidate.step_distance_m == pytest.approx(0.10)
    assert candidate.expected_frequency_regions == ((152.0, 168.0),)
    assert candidate.required_measurements == ("LEFT", "RIGHT", "STEREO")


def test_sbir_without_geometry_or_distance_does_not_invent_test():
    result = AcousticHypothesisExperimentGenerator().generate(
        sbir_context(with_distance=False)
    )
    assert result.ordered_experiments == ()
    assert result.hypotheses[0].uncertainty_reasons == (
        "NO_SAFE_CONCRETE_EXPERIMENT_FROM_AVAILABLE_STRUCTURE",
    )


def test_reflection_surface_generates_one_reversible_localized_treatment():
    result = AcousticHypothesisExperimentGenerator().generate(reflection_context())
    candidate = result.ordered_experiments[0]
    assert candidate.experiment_type is (
        GeneratedExperimentType.LEFT_FIRST_REFLECTION_TEMPORARY_ABSORPTION
    )
    assert candidate.step_distance_m is None
    assert candidate.expected_time_regions == ((4.6, 5.4),)
    assert len(candidate.modified_variables) == 1
    assert "NO_GLOBAL_IMPROVEMENT_GUARANTEE" in candidate.rationale_codes


def test_reflection_without_surface_does_not_propose_massive_treatment():
    result = AcousticHypothesisExperimentGenerator().generate(
        reflection_context(with_surface=False)
    )
    assert result.ordered_experiments == ()


def test_executed_temporary_treatment_is_deduplicated():
    result = AcousticHypothesisExperimentGenerator().generate(
        reflection_context(executed=True)
    )
    assert result.ordered_experiments == ()


def test_mixed_executed_treatment_weakens_hypothesis_without_reproposing_it():
    result = AcousticHypothesisExperimentGenerator().generate(
        reflection_context(mixed=True)
    )
    assert result.ordered_experiments == ()
    assert result.hypotheses[0].status is GeneratedHypothesisStatus.WEAKLY_PLAUSIBLE
    assert "PRIOR_RELATED_TEMPORARY_TREATMENT_MIXED" in (
        result.hypotheses[0].uncertainty_reasons
    )


def test_modal_need_generates_multi_position_without_invented_distance():
    result = AcousticHypothesisExperimentGenerator().generate(modal_context())
    candidate = result.ordered_experiments[0]
    assert candidate.experiment_type is GeneratedExperimentType.LISTENING_POSITION_MULTI_POINT
    assert candidate.step_distance_m is None
    assert candidate.movement_direction is None
    assert candidate.expected_frequency_regions == ((20.0, 50.0),)


def test_executed_multi_position_is_not_reproposed():
    result = AcousticHypothesisExperimentGenerator().generate(
        modal_context(executed=True)
    )
    assert result.ordered_experiments == ()


@pytest.mark.parametrize(
    "outcome,expected_reason",
    [
        (CausalDiscriminationOutcome.INCONCLUSIVE, "CAUSAL_PROTOCOL_NOT_YET_DISCRIMINATED"),
        (CausalDiscriminationOutcome.DISCRIMINATED, "CAUSAL_PROTOCOL_ALREADY_DISCRIMINATED"),
    ],
)
def test_asymmetry_records_causal_discrimination_without_reproposing_swaps(
    outcome, expected_reason
):
    source = hypothesis(HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION)
    result = AcousticHypothesisExperimentGenerator().generate(
        context(
            source,
            causal_discrimination_analysis=SimpleNamespace(outcome=outcome),
        )
    )
    assert result.ordered_experiments == ()
    assert expected_reason in result.hypotheses[0].uncertainty_reasons
    assert all("SWAP" not in item.value for item in GeneratedExperimentType)


def test_one_localized_reflection_experiment_can_explicitly_test_two_hypotheses():
    reflection = reflection_context()
    asymmetry = hypothesis(HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION)
    reflection.acoustic_reasoning_analysis = AcousticReasoningAnalysis(
        hypotheses=(
            reflection.acoustic_reasoning_analysis.hypotheses[0], asymmetry
        ),
        source_analyses=("TestAnalysis",),
        confidence=75.0,
    )
    result = AcousticHypothesisExperimentGenerator().generate(reflection)
    candidate = result.ordered_experiments[0]
    assert "MULTI_PURPOSE_ASYMMETRY_TEST" in candidate.rationale_codes
    assert all(
        candidate.candidate_id in item.experiment_candidate_ids
        for item in result.hypotheses
    )


def test_ranking_is_deterministic_limited_and_has_one_recommendation():
    combined = modal_context()
    sbir = sbir_context()
    combined.acoustic_reasoning_analysis = AcousticReasoningAnalysis(
        hypotheses=(
            *combined.acoustic_reasoning_analysis.hypotheses,
            *sbir.acoustic_reasoning_analysis.hypotheses,
        ),
        source_analyses=("TestAnalysis",),
        confidence=75.0,
    )
    combined.sbir_geometry_correlation_analysis = sbir.sbir_geometry_correlation_analysis
    generator = AcousticHypothesisExperimentGenerator()
    first = generator.generate(combined)
    second = generator.generate(combined)
    assert first == second
    assert len(first.ordered_experiments) <= 5
    assert sum(
        item.candidate_id == first.recommended_candidate_id
        for item in first.ordered_experiments
    ) == 1


def test_expected_observations_cover_all_outcomes_and_never_guarantee_improvement():
    candidate = AcousticHypothesisExperimentGenerator().generate(modal_context()).ordered_experiments[0]
    assert {item.outcome.value for item in candidate.expected_observations} == {
        "SUPPORTING", "CONTRADICTING", "NEUTRAL", "INCONCLUSIVE"
    }
    serialized = repr(candidate).upper()
    assert "GUARANTEED_IMPROVEMENT" not in serialized
    assert "CONFIRMED_CAUSE" not in serialized
    assert candidate.causality_status == "NOT_ESTABLISHED"


def test_model_rejects_other_causality_and_incomplete_channels():
    base = AcousticHypothesisExperimentGenerator().generate(modal_context()).ordered_experiments[0]
    values = dict(base.__dict__)
    values["causality_status"] = "ESTABLISHED"
    with pytest.raises(ValueError):
        GeneratedAcousticExperiment(**values)
    values = dict(base.__dict__)
    values["required_measurements"] = ("LEFT", "RIGHT")
    with pytest.raises(ValueError):
        GeneratedAcousticExperiment(**values)


def test_stage_does_not_mutate_source_analyses_scores_or_recommendations():
    source_context = modal_context()
    source_context.recommendation_analysis = SimpleNamespace(recommendations=("unchanged",))
    source_context.global_analysis = SimpleNamespace(score=51.3)
    before = deepcopy((
        source_context.acoustic_reasoning_analysis,
        source_context.recommendation_analysis,
        source_context.global_analysis,
    ))
    AcousticHypothesisExperimentGenerationStage().run(source_context)
    after = (
        source_context.acoustic_reasoning_analysis,
        source_context.recommendation_analysis,
        source_context.global_analysis,
    )
    assert after == before


def test_presenter_exports_structured_hypotheses_experiments_and_blockages():
    source_context = modal_context()
    AcousticHypothesisExperimentGenerationStage().run(source_context)
    presented = AcousticHypothesisExperimentGenerationPresenter().present(source_context)
    payload = presented.to_dict()
    assert payload["hypotheses"][0]["causality_status"] == "NOT_ESTABLISHED"
    assert payload["experiments"][0]["required_measurements"] == (
        "LEFT", "RIGHT", "STEREO"
    )
    assert payload["recommended_candidate_id"] is not None


def test_real_analogue_deduplicates_swaps_and_left_absorption_then_recommends_new_test():
    early = hypothesis(HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION)
    asymmetry = hypothesis(HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION)
    modal = hypothesis(
        HypothesisCode.MODAL_BASS_PERSISTENCE,
        status=HypothesisStatus.INCONCLUSIVE,
        support=False,
        context=True,
    )
    source_context = context(
        early,
        asymmetry,
        modal,
        modal_density_analysis=SimpleNamespace(
            sparse_bands=[SimpleNamespace(minimum_hz=20.0, maximum_hz=50.0)],
            dense_bands=[],
        ),
        experiment_descriptors=(
            descriptor("LOUDSPEAKER_ASSIGNMENT"),
            descriptor("SIGNAL_CHAIN_ASSIGNMENT"),
            descriptor("TEMPORARY_LEFT_FIRST_REFLECTION_ABSORPTION"),
        ),
        causal_discrimination_analysis=SimpleNamespace(
            outcome=CausalDiscriminationOutcome.DISCRIMINATED
        ),
    )
    result = AcousticHypothesisExperimentGenerator().generate(source_context)
    assert tuple(item.experiment_type for item in result.ordered_experiments) == (
        GeneratedExperimentType.LISTENING_POSITION_MULTI_POINT,
    )
    assert result.recommended_candidate_id == result.ordered_experiments[0].candidate_id
    assert all(item.causality_status == "NOT_ESTABLISHED" for item in result.hypotheses)


def test_pipeline_and_report_expose_generation_without_changing_existing_projection():
    report = AcousticBrain().analyze(reference_project())
    generated = report.acoustic_hypothesis_experiment_generation
    assert generated is not None
    assert len(generated.hypotheses) <= 5
    assert len(generated.experiments) <= 5
    assert report.global_analysis is not None
    assert report.recommendations
