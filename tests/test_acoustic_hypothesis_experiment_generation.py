from copy import deepcopy
from dataclasses import replace
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
    ImpulseChannel,
    MeasurementQualityAnalysis,
    MeasurementSetQuality,
    ListeningPositionSamplingPosition,
    ListeningPositionSamplingProtocol,
    Peak,
    REQUIRED_COMPLETION_CONDITION_CODES,
    RecommendationPriority,
    ReasoningEvidence,
    ReflectionCandidateGeometricStatus,
    RoomSurfaceKind,
    VerificationAction,
    VerificationActionType,
)
from acousticbrain.report import (
    AcousticHypothesisExperimentGenerationPresenter,
    ConsoleReporter,
    Report,
)
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


def hypothesis(
    code,
    *,
    status=HypothesisStatus.SUPPORTED,
    support=True,
    context=False,
    action_parameters=None,
):
    supporting_evidence = (evidence(f"{code.value}.support"),) if support else ()
    verification_actions = ()
    if action_parameters is not None:
        verification_actions = (
            VerificationAction(
                code=f"VERIFY_{code.value}",
                action_type=VerificationActionType.TEMPORARY_MOVE,
                target="structured_test_target",
                priority=RecommendationPriority.HIGH,
                confidence=75.0,
                evidence_fact_codes=tuple(
                    item.fact_code for item in supporting_evidence
                ),
                expected_supporting_fact_codes=("EXPECTED_SUPPORT",),
                expected_counter_fact_codes=("EXPECTED_COUNTER",),
                parameters=action_parameters,
            ),
        )
    return AcousticHypothesis(
        code=code,
        phenomenon=code.value,
        domain_codes=("TEST",),
        supporting_evidence=supporting_evidence,
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
        verification_actions=verification_actions,
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
        measurement_quality_analysis=MeasurementQualityAnalysis(
            measurement_set_quality=MeasurementSetQuality(
                available_channels=(
                    ImpulseChannel.LEFT,
                    ImpulseChannel.RIGHT,
                    ImpulseChannel.STEREO,
                ),
                required_channels=(
                    ImpulseChannel.LEFT,
                    ImpulseChannel.RIGHT,
                    ImpulseChannel.STEREO,
                ),
                confidence=100.0,
            ),
            confidence=100.0,
        ),
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


def sampling_protocol():
    measurements = ("LEFT", "RIGHT", "STEREO")
    return ListeningPositionSamplingProtocol(
        protocol_id="protocol.listening_position_sampling.v1",
        version=1,
        positions=(
            ListeningPositionSamplingPosition(
                "REFERENCE", "REFERENCE", 0.0, None, None,
                None, "REFERENCE", 1, measurements,
            ),
            ListeningPositionSamplingPosition(
                "FORWARD_100MM", "FORWARD", 0.10, None, None,
                "REFERENCE", "REFERENCE", 2, measurements,
            ),
            ListeningPositionSamplingPosition(
                "BACKWARD_100MM", "BACKWARD", -0.10, None, None,
                "FORWARD_100MM", "REFERENCE", 3, measurements,
            ),
        ),
        modified_variables=("LISTENING_POSITION",),
        controlled_variables=(
            "LOUDSPEAKER_POSITION",
            "LOUDSPEAKER_ASSIGNMENT",
            "SIGNAL_CHAIN_ASSIGNMENT",
            "ROOM_CONFIGURATION",
            "MICROPHONE_ORIENTATION",
            "MEASUREMENT_LEVEL",
            "REW_PARAMETERS",
        ),
        comparability_rule_code="LISTENING_POSITION_ORDERED_REFERENCE_BRANCH",
        completion_condition_codes=REQUIRED_COMPLETION_CONDITION_CODES,
    )


def modal_context(
    *,
    executed=False,
    source=None,
    available_channels=None,
    with_sampling_geometry=True,
):
    source = source or hypothesis(
        HypothesisCode.MODAL_BASS_PERSISTENCE,
        status=HypothesisStatus.INCONCLUSIVE,
        support=False,
        context=True,
    )
    band = SimpleNamespace(minimum_hz=20.0, maximum_hz=50.0)
    values = {}
    if available_channels is not None:
        values["measurement_quality_analysis"] = MeasurementQualityAnalysis(
            measurement_set_quality=MeasurementSetQuality(
                available_channels=tuple(available_channels),
                required_channels=(
                    ImpulseChannel.LEFT,
                    ImpulseChannel.RIGHT,
                    ImpulseChannel.STEREO,
                ),
                confidence=100.0,
            ),
            confidence=100.0,
        )
    descriptors = ()
    if executed:
        descriptors = (*descriptors, descriptor("LISTENING_POSITION_MULTI_POINT"))
    return context(
        source,
        modal_density_analysis=SimpleNamespace(sparse_bands=[band], dense_bands=[]),
        experiment_descriptors=descriptors,
        listening_position_sampling_protocol=(
            sampling_protocol() if with_sampling_geometry else None
        ),
        **values,
    )


def reflection_context(
    *, executed=False, mixed=False, with_surface=True, uncertainty_ms=0.4
):
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
                path_id="path.left", theoretical_delay_ms=5.0,
                uncertainty_ms=uncertainty_ms
            ),)
        ),
        experiment_descriptors=(
            descriptor("TEMPORARY_LEFT_FIRST_REFLECTION_ABSORPTION"),
        ) if executed or mixed else (),
        experiment_comparison_analysis=comparison,
    )


def sbir_context(
    *, with_distance=True, step_distance_m=0.10, frequency_uncertainty_hz=8.0
):
    parameters = (
        {}
        if step_distance_m is None
        else {"proposed_displacement_m": step_distance_m}
    )
    source = hypothesis(
        HypothesisCode.SBIR_PLACEMENT_INTERACTION,
        action_parameters=parameters,
    )
    if not with_distance:
        return context(source)
    candidate = SimpleNamespace(
        surface=SimpleNamespace(name="FRONT_WALL"),
        speaker_id="LEFT_SPEAKER",
        speaker_boundary_distance_m=0.54,
        frequency_uncertainty_hz=frequency_uncertainty_hz,
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


def test_sbir_reuses_structured_step_distance_without_transforming_it():
    result = AcousticHypothesisExperimentGenerator().generate(
        sbir_context(step_distance_m=0.12, frequency_uncertainty_hz=3.0)
    )
    candidate = result.ordered_experiments[0]
    assert candidate.experiment_type is GeneratedExperimentType.LEFT_SPEAKER_FORWARD
    assert candidate.movement_direction == "FORWARD_AWAY_FROM_FRONT_WALL"
    assert candidate.step_distance_m == pytest.approx(0.12)
    assert candidate.expected_frequency_regions == ((157.0, 163.0),)
    assert candidate.blocking_reasons == ()
    assert candidate.required_measurements == ("LEFT", "RIGHT", "STEREO")


def test_sbir_without_geometry_or_distance_does_not_invent_test():
    result = AcousticHypothesisExperimentGenerator().generate(
        sbir_context(with_distance=False)
    )
    assert result.ordered_experiments == ()
    assert result.hypotheses[0].uncertainty_reasons == (
        "NO_SAFE_CONCRETE_EXPERIMENT_FROM_AVAILABLE_STRUCTURE",
    )


def test_sbir_without_structured_amplitude_is_blocked_and_invents_no_distance():
    result = AcousticHypothesisExperimentGenerator().generate(
        sbir_context(step_distance_m=None)
    )
    candidate = result.ordered_experiments[0]
    assert candidate.step_distance_m is None
    assert candidate.blocking_reasons == ("STRUCTURED_STEP_DISTANCE_UNAVAILABLE",)
    assert result.recommended_candidate_id is None
    assert "0.05" not in repr(candidate)
    assert "0.10" not in repr(candidate)


def test_sbir_frequency_region_comes_from_structured_source_uncertainty():
    candidate = AcousticHypothesisExperimentGenerator().generate(
        sbir_context(frequency_uncertainty_hz=1.25)
    ).ordered_experiments[0]
    assert candidate.expected_frequency_regions == ((158.75, 161.25),)


def test_sbir_without_structured_frequency_uncertainty_has_no_region():
    candidate = AcousticHypothesisExperimentGenerator().generate(
        sbir_context(frequency_uncertainty_hz=None)
    ).ordered_experiments[0]
    assert candidate.expected_frequency_regions == ()


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


def test_reflection_without_structured_time_uncertainty_has_no_region():
    candidate = AcousticHypothesisExperimentGenerator().generate(
        reflection_context(uncertainty_ms=None)
    ).ordered_experiments[0]
    assert candidate.expected_time_regions == ()


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
    assert candidate.reference_position_id == "REFERENCE"
    assert candidate.comparability_rule_code == (
        "LISTENING_POSITION_ORDERED_REFERENCE_BRANCH"
    )
    assert candidate.sampling_protocol_id == "protocol.listening_position_sampling.v1"
    assert candidate.sampling_protocol_version == 1
    assert candidate.modified_variables == ("LISTENING_POSITION",)
    assert tuple(
        (
            item.position_id,
            item.role,
            item.longitudinal_offset_m,
            item.lateral_offset_m,
            item.vertical_offset_m,
            item.parent_position_id,
            item.reference_position_id,
        )
        for item in candidate.acquisition_positions
    ) == (
        ("REFERENCE", "REFERENCE", 0.0, None, None, None, "REFERENCE"),
        (
            "FORWARD_100MM", "FORWARD", 0.10, None, None,
            "REFERENCE", "REFERENCE",
        ),
        (
            "BACKWARD_100MM", "BACKWARD", -0.10, None, None,
            "FORWARD_100MM", "REFERENCE",
        ),
    )
    assert all(
        item.required_measurements == ("LEFT", "RIGHT", "STEREO")
        for item in candidate.acquisition_positions
    )


def test_modal_candidate_without_structured_sampling_geometry_is_blocked():
    result = AcousticHypothesisExperimentGenerator().generate(
        modal_context(with_sampling_geometry=False)
    )
    candidate = result.ordered_experiments[0]
    assert candidate.acquisition_positions == ()
    assert candidate.reference_position_id is None
    assert candidate.blocking_reasons == (
        "MULTI_POSITION_SAMPLING_GEOMETRY_UNAVAILABLE",
    )
    assert result.recommended_candidate_id is None


def test_report_describes_protocol_branch_without_creating_experiments(capsys):
    source_context = modal_context()
    AcousticHypothesisExperimentGenerationStage().run(source_context)
    report = Report(project_name="sampling-protocol")
    report.acoustic_hypothesis_experiment_generation = (
        AcousticHypothesisExperimentGenerationPresenter().present(source_context)
    )

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert "Campagne proposée" in output
    assert "REFERENCE (longitudinal +0.00 m)" in output
    assert "FORWARD_100MM (longitudinal +0.10 m)" in output
    assert "BACKWARD_100MM (longitudinal -0.10 m)" in output
    assert output.index("REFERENCE (longitudinal +0.00 m)") < output.index(
        "FORWARD_100MM (longitudinal +0.10 m)"
    ) < output.index("BACKWARD_100MM (longitudinal -0.10 m)")
    assert "Mesures : LEFT, RIGHT, STEREO" in output
    assert "exp-008" not in output


@pytest.mark.parametrize(
    "source_status,expected_status",
    [
        (HypothesisStatus.INCONCLUSIVE, GeneratedHypothesisStatus.INSUFFICIENT_EVIDENCE),
        (HypothesisStatus.CONTRADICTED, GeneratedHypothesisStatus.CONTRADICTED),
    ],
)
def test_modal_non_supporting_status_is_not_eligible_despite_available_bands(
    source_status, expected_status
):
    source = hypothesis(
        HypothesisCode.MODAL_BASS_PERSISTENCE,
        status=source_status,
        support=False,
        context=False,
    )
    result = AcousticHypothesisExperimentGenerator().generate(
        modal_context(source=source)
    )
    assert result.ordered_experiments == ()
    assert result.hypotheses[0].status is expected_status


def test_modal_hypothesis_without_targeted_measured_anomaly_has_no_candidate():
    source = hypothesis(HypothesisCode.MODAL_BASS_PERSISTENCE)
    result = AcousticHypothesisExperimentGenerator().generate(context(source))
    assert result.ordered_experiments == ()


@pytest.mark.parametrize(
    "missing_channel",
    [ImpulseChannel.LEFT, ImpulseChannel.RIGHT, ImpulseChannel.STEREO],
)
def test_modal_candidate_is_blocked_when_a_required_measurement_is_missing(
    missing_channel,
):
    available = tuple(
        channel
        for channel in (
            ImpulseChannel.LEFT,
            ImpulseChannel.RIGHT,
            ImpulseChannel.STEREO,
        )
        if channel is not missing_channel
    )
    result = AcousticHypothesisExperimentGenerator().generate(
        modal_context(available_channels=available)
    )
    candidate = result.ordered_experiments[0]
    assert candidate.blocking_reasons == (
        f"REQUIRED_MEASUREMENT_UNAVAILABLE:{missing_channel.value}",
    )
    assert result.recommended_candidate_id is None


def test_modal_candidate_is_eligible_with_left_right_and_stereo_available():
    result = AcousticHypothesisExperimentGenerator().generate(modal_context())
    candidate = result.ordered_experiments[0]
    assert candidate.blocking_reasons == ()
    assert result.recommended_candidate_id == candidate.candidate_id


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


def test_ranking_caps_exactly_at_five_with_more_than_five_candidates():
    generator = AcousticHypothesisExperimentGenerator()
    base = generator.generate(modal_context()).ordered_experiments[0]
    candidates = tuple(
        replace(base, candidate_id=f"generated.modal.{index}")
        for index in range(6)
    )
    ranked = generator._rank_and_limit(reversed(candidates))
    assert len(ranked) == 5
    assert tuple(item.candidate_id for item in ranked) == tuple(
        f"generated.modal.{index}" for index in range(5)
    )


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
    source_context.causal_discrimination_analysis = SimpleNamespace(
        outcome=CausalDiscriminationOutcome.INCONCLUSIVE,
        marker="unchanged",
    )
    source_context.longitudinal_experimental_learning_analysis = SimpleNamespace(
        state="STABLE_NON_SUPPORT",
        marker="unchanged",
    )
    source_references = (
        source_context.acoustic_reasoning_analysis,
        source_context.recommendation_analysis,
        source_context.global_analysis,
        source_context.causal_discrimination_analysis,
        source_context.longitudinal_experimental_learning_analysis,
        source_context.modal_density_analysis,
        source_context.measurement_quality_analysis,
    )
    before = deepcopy((
        source_context.acoustic_reasoning_analysis,
        source_context.recommendation_analysis,
        source_context.global_analysis,
        source_context.causal_discrimination_analysis,
        source_context.longitudinal_experimental_learning_analysis,
        source_context.modal_density_analysis,
        source_context.measurement_quality_analysis,
    ))
    AcousticHypothesisExperimentGenerationStage().run(source_context)
    after = (
        source_context.acoustic_reasoning_analysis,
        source_context.recommendation_analysis,
        source_context.global_analysis,
        source_context.causal_discrimination_analysis,
        source_context.longitudinal_experimental_learning_analysis,
        source_context.modal_density_analysis,
        source_context.measurement_quality_analysis,
    )
    assert after == before
    assert all(current is original for current, original in zip(after, source_references))


def test_presenter_exports_structured_hypotheses_experiments_and_blockages():
    source_context = modal_context()
    AcousticHypothesisExperimentGenerationStage().run(source_context)
    presented = AcousticHypothesisExperimentGenerationPresenter().present(source_context)
    payload = presented.to_dict()
    assert payload["hypotheses"][0]["causality_status"] == "NOT_ESTABLISHED"
    assert payload["experiments"][0]["required_measurements"] == (
        "LEFT", "RIGHT", "STEREO"
    )
    assert len(payload["experiments"][0]["acquisition_positions"]) == 3
    assert payload["recommended_candidate_id"] is not None


def test_real_analogue_blocks_modal_candidate_without_sampling_geometry():
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
    assert result.ordered_experiments[0].blocking_reasons == (
        "MULTI_POSITION_SAMPLING_GEOMETRY_UNAVAILABLE",
    )
    assert result.recommended_candidate_id is None
    assert all(item.causality_status == "NOT_ESTABLISHED" for item in result.hypotheses)


def test_pipeline_and_report_expose_generation_without_changing_existing_projection():
    report = AcousticBrain().analyze(reference_project())
    generated = report.acoustic_hypothesis_experiment_generation
    assert generated is not None
    assert len(generated.hypotheses) <= 5
    assert len(generated.experiments) <= 5
    assert report.global_analysis is not None
    assert report.recommendations


def test_integrated_report_exposes_exactly_one_main_action_label(capsys):
    report = AcousticBrain().analyze(reference_project(), plan_experiments=True)

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert output.lower().count("expérience principale") == 1
    assert "PRIORITAIRE" not in output
