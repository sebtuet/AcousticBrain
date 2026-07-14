from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

from acousticbrain.analysis import AcousticReasoningEngine, ExperimentPlanner
from acousticbrain.models import (
    AcousticHypothesis,
    AcousticReasoningAnalysis,
    EvidenceRole,
    ExperimentCostCategory,
    ExperimentDifficulty,
    ExperimentProtocol,
    ExperimentReversibility,
    ExperimentSelectionReason,
    HypothesisCode,
    HypothesisStatus,
    MissingReasoningFact,
    ReasoningEvidence,
    RecommendationPriority,
    VerificationAction,
    VerificationActionType,
)


ACTION_DATA = {
    HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION: (
        "VERIFY_SPEAKER_ROOM_ASYMMETRY",
        VerificationActionType.COMPARE,
        {},
    ),
    HypothesisCode.MODAL_BASS_PERSISTENCE: (
        "VERIFY_MODAL_BASS_PERSISTENCE",
        VerificationActionType.MEASURE,
        {},
    ),
    HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION: (
        "VERIFY_DOMINANT_EARLY_REFLECTION",
        VerificationActionType.TEMPORARY_MASK,
        {
            "surface": "LEFT_SIDE_WALL_PANEL_02",
            "observed_channel": "LEFT",
            "observed_event_delay_ms": 3.0,
            "observed_event_relative_level_db": -7.4,
            "theoretical_delay_ms": 2.86,
            "timing_error_ms": 0.14,
            "geometry_uncertainty_ms": 0.2,
            "geometry_confidence": 88.0,
            "geometry_path_id": "geometry_reflection.LEFT.MIC.LEFT_SIDE_WALL_PANEL_02",
        },
    ),
    HypothesisCode.SBIR_PLACEMENT_INTERACTION: (
        "VERIFY_SBIR_PLACEMENT",
        VerificationActionType.TEMPORARY_MOVE,
        {
            "surface": "FRONT_WALL",
            "measured_frequency_hz": 85.0,
            "current_distance_m": 1.0,
        },
    ),
}


def hypothesis(
    code,
    *,
    status=HypothesisStatus.PLAUSIBLE,
    support=50.0,
    confidence=80.0,
    action=True,
    parameters=None,
    missing=(),
    counter_count=0,
):
    evidence = ReasoningEvidence(
        code=f"reasoning.{code.value.lower()}.source",
        role=EvidenceRole.SUPPORTING,
        fact_code=f"fact.{code.value.lower()}",
        source_analysis="StructuredAnalysis",
        value=support,
        strength=support,
        confidence=confidence,
    )
    counters = tuple(
        ReasoningEvidence(
            code=f"reasoning.{code.value.lower()}.counter.{index}",
            role=EvidenceRole.COUNTER_EVIDENCE,
            fact_code=f"counter.{code.value.lower()}.{index}",
            source_analysis="StructuredAnalysis",
            value=index,
            strength=20.0,
            confidence=confidence,
        )
        for index in range(counter_count)
    )
    actions = ()
    if action:
        action_code, action_type, default_parameters = ACTION_DATA[code]
        actions = (
            VerificationAction(
                code=action_code,
                action_type=action_type,
                target="structured_target",
                priority=RecommendationPriority.MEDIUM,
                confidence=confidence,
                evidence_fact_codes=(evidence.fact_code,),
                expected_supporting_fact_codes=("verification.support",),
                expected_counter_fact_codes=("verification.counter",),
                parameters=(
                    default_parameters if parameters is None else parameters
                ),
            ),
        )
    return AcousticHypothesis(
        code=code,
        phenomenon="structured_phenomenon",
        domain_codes=("TEST",),
        supporting_evidence=(evidence,),
        counter_evidence=counters,
        context_evidence=(),
        missing_facts=tuple(
            MissingReasoningFact(
                fact_code=fact_code,
                source_analysis="StructuredAnalysis",
                rule_code=f"MISSING_{index}",
            )
            for index, fact_code in enumerate(missing)
        ),
        applied_rule_codes=("STRUCTURED_RULE",),
        support_score=support,
        confidence=confidence,
        status=status,
        verification_actions=actions,
    )


def analysis(*hypotheses):
    return AcousticReasoningAnalysis(
        hypotheses=tuple(hypotheses),
        source_analyses=("StructuredAnalysis",),
        confidence=80.0,
    )


def candidate(result, code):
    return next(
        item
        for item in (
            *result.plan.ordered_candidates,
            *result.plan.ineligible_candidates,
        )
        if item.hypothesis_code == code.value
    )


@pytest.mark.parametrize(
    ("override", "reason"),
    (
        (
            {"timing_error_ms": 1.01},
            ExperimentSelectionReason.GEOMETRY_TIMING_INCOMPATIBLE,
        ),
        (
            {"geometry_uncertainty_ms": 0.51},
            ExperimentSelectionReason.GEOMETRY_UNCERTAINTY_TOO_HIGH,
        ),
        (
            {"geometry_confidence": 69.9},
            ExperimentSelectionReason.GEOMETRY_CONFIDENCE_TOO_LOW,
        ),
    ),
)
def test_early_reflection_protocol_enforces_geometry_quality(override, reason):
    parameters = dict(
        ACTION_DATA[HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION][2]
    )
    parameters.update(override)
    result = ExperimentPlanner().plan(analysis(hypothesis(
        HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION,
        parameters=parameters,
    )))

    item = candidate(
        result, HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION
    )

    assert item.eligible is False
    assert reason in item.ineligibility_reasons


def test_early_reflection_protocol_preserves_testable_surface_parameters():
    result = ExperimentPlanner().plan(analysis(hypothesis(
        HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION,
    )))

    item = candidate(
        result, HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION
    )

    assert item.eligible is True
    assert item.source_protocol_id == "protocol.temporary_mask_surface.v1"
    assert item.parameters["surface"] == "LEFT_SIDE_WALL_PANEL_02"
    assert item.parameters["timing_error_ms"] == 0.14
    assert item.changed_variable_codes == ("SURFACE_MASKING_STATE",)
    assert "MICROPHONE_POSITION" in item.controlled_variable_codes
    assert "LOUDSPEAKER_ORIENTATION" in item.controlled_variable_codes


def test_planner_classifies_the_four_initial_experiments():
    reasoning = AcousticReasoningEngine().analyze()

    result = ExperimentPlanner().plan(reasoning)

    all_candidates = (
        *result.plan.ordered_candidates,
        *result.plan.ineligible_candidates,
    )
    assert {item.hypothesis_code for item in all_candidates} == {
        item.value for item in HypothesisCode
    }
    assert result.plan.recommended_candidate.hypothesis_code == (
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION.value
    )


def test_planner_excludes_action_explicitly_deferred_by_user():
    result = ExperimentPlanner().plan(
        AcousticReasoningEngine().analyze(),
        deferred_action_codes=("VERIFY_SPEAKER_ROOM_ASYMMETRY",),
    )

    asymmetry = candidate(
        result, HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION
    )
    assert asymmetry.eligible is False
    assert ExperimentSelectionReason.USER_DEFERRED in (
        asymmetry.ineligibility_reasons
    )
    assert result.plan.recommended_candidate is not asymmetry


def test_planner_excludes_protocol_completed_by_discovered_experiments():
    result = ExperimentPlanner().plan(
        AcousticReasoningEngine().analyze(),
        completed_protocol_ids=(
            "protocol.verify_modal_bass_persistence.v1",
        ),
    )

    modal = candidate(result, HypothesisCode.MODAL_BASS_PERSISTENCE)
    assert modal.eligible is False
    assert ExperimentSelectionReason.ALREADY_COMPLETED in (
        modal.ineligibility_reasons
    )


def test_information_value_is_not_the_support_score():
    item = candidate(
        ExperimentPlanner().plan(
            analysis(
                hypothesis(
                    HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
                    support=50.0,
                )
            )
        ),
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
    )

    assert item.informative_value != item.support_score


def test_difficulty_cost_and_duration_are_penalties():
    planner = ExperimentPlanner()
    common = dict(
        support_score=50.0,
        confidence=80.0,
        missing_fact_count=2,
        resolved_missing_fact_count=2,
        counter_evidence_count=1,
        discriminated_hypothesis_count=2,
        reversibility=ExperimentReversibility.HIGH,
        repetition_count=0,
    )
    simple = planner.informative_value(
        **common,
        difficulty=ExperimentDifficulty.EASY,
        duration_minutes=15,
        cost=ExperimentCostCategory.FREE,
    )
    costly = planner.informative_value(
        **common,
        difficulty=ExperimentDifficulty.HARD,
        duration_minutes=90,
        cost=ExperimentCostCategory.HIGH,
    )

    assert simple > costly


def test_reversibility_increases_information_value():
    common = dict(
        support_score=50.0,
        confidence=80.0,
        missing_fact_count=0,
        resolved_missing_fact_count=0,
        counter_evidence_count=0,
        discriminated_hypothesis_count=1,
        difficulty=ExperimentDifficulty.EASY,
        duration_minutes=None,
        cost=ExperimentCostCategory.FREE,
    )

    high = ExperimentPlanner.informative_value(
        **common, reversibility=ExperimentReversibility.HIGH
    )
    low = ExperimentPlanner.informative_value(
        **common, reversibility=ExperimentReversibility.LOW
    )

    assert high > low


def test_geometry_prerequisites_are_not_invented():
    sbir = hypothesis(
        HypothesisCode.SBIR_PLACEMENT_INTERACTION,
        parameters={"surface": "FRONT_WALL", "measured_frequency_hz": 85.0},
    )

    item = candidate(
        ExperimentPlanner().plan(analysis(sbir)),
        HypothesisCode.SBIR_PLACEMENT_INTERACTION,
    )

    assert item.eligible is False
    assert "current_distance_m" in item.unmet_prerequisite_codes
    assert not hasattr(item, "current_distance_m")


def test_completed_experiment_is_ineligible_and_penalized():
    asymmetry = hypothesis(
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION
    )
    session = SimpleNamespace(
        iterations=(
            SimpleNamespace(
                is_completed=True,
                protocol=ExperimentProtocol(
                    experiment_id="past-experiment",
                    hypothesis_code=asymmetry.code.value,
                    action_code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
                    label="Past explicit experiment",
                    fact_codes=(),
                ),
            ),
        ),
        pending_iteration=None,
    )

    item = candidate(
        ExperimentPlanner().plan(analysis(asymmetry), session=session),
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
    )
    fresh = candidate(
        ExperimentPlanner().plan(analysis(asymmetry)),
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
    )

    assert item.eligible is False
    assert item.informative_value < fresh.informative_value
    assert "ALREADY_COMPLETED" in {
        reason.value for reason in item.ineligibility_reasons
    }


def test_supported_hypothesis_is_adapted_but_not_declared_confirmed():
    supported = hypothesis(
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
        status=HypothesisStatus.SUPPORTED,
        support=90.0,
    )

    item = candidate(
        ExperimentPlanner().plan(analysis(supported)),
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
    )

    assert item.eligible is True
    assert item.hypothesis_status == "SUPPORTED"
    assert item.informative_value < item.support_score


def test_contradicted_hypothesis_is_ineligible():
    contradicted = hypothesis(
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
        status=HypothesisStatus.CONTRADICTED,
        support=10.0,
        action=False,
    )

    item = candidate(
        ExperimentPlanner().plan(analysis(contradicted)),
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
    )

    assert item.eligible is False
    assert "HYPOTHESIS_REFUTED" in {
        reason.value for reason in item.ineligibility_reasons
    }


def test_inconclusive_hypothesis_can_use_investigation_protocol():
    inconclusive = hypothesis(
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
        status=HypothesisStatus.INCONCLUSIVE,
        support=10.0,
        action=False,
        missing=("stereo.symmetry_score",),
    )

    item = candidate(
        ExperimentPlanner().plan(analysis(inconclusive)),
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
    )

    assert item.eligible is True
    assert item.source_action_code is None
    assert item.source_protocol_id.startswith("protocol.")


def test_equal_candidates_are_sorted_by_stable_identifier():
    result = ExperimentPlanner().plan(
        analysis(
            hypothesis(
                HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION
            )
        )
    )
    base = candidate(
        result,
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION,
    )
    candidates = (
        replace(base, candidate_id="experiment_candidate.z"),
        replace(base, candidate_id="experiment_candidate.a"),
    )

    ordered = sorted(candidates, key=ExperimentPlanner._sort_key)

    assert [item.candidate_id for item in ordered] == [
        "experiment_candidate.a",
        "experiment_candidate.z",
    ]


def test_planning_models_are_immutable_and_do_not_create_a_session():
    reasoning = AcousticReasoningEngine().analyze()
    result = ExperimentPlanner().plan(reasoning)

    with pytest.raises(FrozenInstanceError):
        result.status = None
    assert isinstance(result.plan.ordered_candidates, tuple)
    assert not hasattr(result, "session")


def test_trace_links_reference_an_explicit_pending_session_iteration():
    asymmetry = hypothesis(
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION
    )
    pending = SimpleNamespace(
        number=3,
        is_completed=False,
        protocol=ExperimentProtocol(
            experiment_id="selected-experiment",
            hypothesis_code=asymmetry.code.value,
            action_code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
            label="Explicit pending experiment",
            fact_codes=(),
        ),
    )
    session = SimpleNamespace(
        iterations=(pending,),
        pending_iteration=pending,
    )

    result = ExperimentPlanner().plan(analysis(asymmetry), session=session)
    trace = next(
        item
        for item in result.trace_links
        if item.hypothesis_code == asymmetry.code.value
    )

    assert trace.session_iteration_number == 3
