import json
from types import SimpleNamespace

import pytest

from acousticbrain.advisor import AdvisorContextBuilder, AdvisorService, MockAdvisorProvider
from acousticbrain.analysis import EvidenceAcquisitionPlanner
from acousticbrain.models import (
    AdvisorAudience,
    AdvisorDetailLevel,
    AdvisorValidationStatus,
    EvidenceAcquisitionEffort,
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionPlanSynthesis,
    EvidenceAcquisitionPriority,
    EvidenceAcquisitionStatus,
    EvidenceAcquisitionTestType,
    EvidenceBlockingFactor,
    EvidenceWeightLevel,
    WeightedActionApplicability,
)
from acousticbrain.report import (
    EvidenceAcquisitionPlanPresenter,
    PresentedEvidenceAcquisitionPlan,
    PresentedEvidenceAcquisitionPlanReport,
    Report,
)


def factor(action_id, code, sources):
    return EvidenceBlockingFactor(
        factor_id=f"blocking.{action_id.lower()}.{code.lower()}",
        code=code,
        source_object_ids=tuple(sources),
        justification=f"Existing upstream state exposes {code}.",
    )


def planner_inputs(
    reasoning_id="ASYMMETRIC_SPEAKER_ROOM_INTERACTION_REASONING",
    factors=(),
    missing=(),
    limitations=(),
    strength=EvidenceWeightLevel.HIGH,
    applicability=WeightedActionApplicability.BLOCKED,
):
    action_id = f"ACTION_{reasoning_id}"
    weight_id = f"EVIDENCE_WEIGHT_{action_id}"
    reasoning = SimpleNamespace(reasoning_id=reasoning_id)
    action = SimpleNamespace(
        action_id=action_id,
        source_reasoning_ids=(reasoning_id,),
        required_missing_parameters=tuple(missing),
        limitations=tuple(limitations),
    )
    weight = SimpleNamespace(
        weight_id=weight_id,
        action_references=(action_id,),
        reasoning_references=(reasoning_id,),
        blocking_factors=tuple(factors),
        limitations=tuple(limitations),
        evidence_strength=strength,
        action_applicability=applicability,
    )
    return (
        SimpleNamespace(reasonings=(reasoning,)),
        SimpleNamespace(actions=(action,)),
        SimpleNamespace(weights=(weight,)),
    )


def contradiction_inputs(reasoning_id="ASYMMETRIC_SPEAKER_ROOM_INTERACTION_REASONING"):
    action_id = f"ACTION_{reasoning_id}"
    contradiction = factor(action_id, "CONTRADICTORY_EVIDENCE", ("evidence.left_right",))
    return planner_inputs(reasoning_id, (contradiction,))


def valid_plan(**overrides):
    values = dict(
        plan_id="EVIDENCE_ACQUISITION_REASONING_TEST",
        reasoning_id="REASONING",
        corrective_action_id="ACTION",
        evidence_weight_id="WEIGHT",
        blocking_factor_ids=("blocking.action.contradictory_evidence",),
        objective="Acquire evidence for an existing blocking factor.",
        test_type=EvidenceAcquisitionTestType.REPEAT_MEASUREMENT,
        instructions=("Repeat the measurement under controlled conditions.",),
        required_inputs=("existing_measurement",),
        controlled_variables=("gain",),
        independent_variables=("repetition",),
        measurements_to_capture=("frequency_response",),
        expected_observations=("repeatability",),
        success_criteria=("The repeated observation is deterministic.",),
        failure_criteria=("Acquisition settings differ.",),
        resulting_evidence_targets=("evidence.target",),
        priority=EvidenceAcquisitionPriority.HIGH,
        estimated_effort=EvidenceAcquisitionEffort.LOW,
        status=EvidenceAcquisitionStatus.READY,
        limitations=("The plan does not change an action.",),
    )
    values.update(overrides)
    return EvidenceAcquisitionPlan(**values)


def test_contradiction_creates_channel_isolation_plan_with_stable_id():
    inputs = contradiction_inputs()
    first = EvidenceAcquisitionPlanner().plan(*inputs)
    second = EvidenceAcquisitionPlanner().plan(*inputs)

    assert first == second
    assert len(first.plans) == 1
    plan = first.plans[0]
    assert plan.test_type is EvidenceAcquisitionTestType.CHANNEL_ISOLATION
    assert plan.status is EvidenceAcquisitionStatus.READY
    assert plan.independent_variables == ("active_channel",)
    assert plan.priority is EvidenceAcquisitionPriority.CRITICAL


def test_modal_factors_are_grouped_when_one_comparison_addresses_both():
    reasoning_id = "MODAL_BASS_PERSISTENCE_REASONING"
    action_id = f"ACTION_{reasoning_id}"
    contradiction = factor(action_id, "CONTRADICTORY_EVIDENCE", ("maximum_decay",))
    discrimination = factor(action_id, "INSUFFICIENT_DISCRIMINATION", (reasoning_id,))
    missing = factor(action_id, "MISSING_PARAMETERS", ("compatible_protocol_or_plan_id",))
    synthesis = EvidenceAcquisitionPlanner().plan(
        *planner_inputs(
            reasoning_id,
            (contradiction, missing, discrimination),
            missing=("compatible_protocol_or_plan_id",),
        )
    )

    assert [value.test_type for value in synthesis.plans] == [
        EvidenceAcquisitionTestType.COMPARATIVE_MEASUREMENT,
        EvidenceAcquisitionTestType.PARAMETER_COMPLETION,
    ]
    assert synthesis.plans[0].blocking_factor_ids == (
        contradiction.factor_id,
        discrimination.factor_id,
    )
    assert all(value.status is EvidenceAcquisitionStatus.BLOCKED for value in synthesis.plans)
    assert all(value.priority is EvidenceAcquisitionPriority.CRITICAL for value in synthesis.plans)


def test_missing_protocol_never_invents_protocol_or_geometry():
    reasoning_id = "DOMINANT_EARLY_REFLECTION_INTERACTION_REASONING"
    action_id = f"ACTION_{reasoning_id}"
    missing = factor(action_id, "MISSING_PARAMETERS", ("compatible_protocol_or_plan_id",))
    plan = EvidenceAcquisitionPlanner().plan(
        *planner_inputs(
            reasoning_id,
            (missing,),
            missing=("compatible_protocol_or_plan_id",),
        )
    ).plans[0]

    assert plan.test_type is EvidenceAcquisitionTestType.PARAMETER_COMPLETION
    assert plan.status is EvidenceAcquisitionStatus.BLOCKED
    assert "does not invent" in " ".join(plan.limitations)
    assert not any(" cm" in value for value in plan.instructions)


def test_sbir_missing_observation_creates_observation_and_geometry_plans():
    reasoning_id = "SBIR_PLACEMENT_INTERACTION_REASONING"
    action_id = f"ACTION_{reasoning_id}"
    missing = factor(action_id, "MISSING_PARAMETERS", ("additional_supporting_observation",))
    synthesis = EvidenceAcquisitionPlanner().plan(
        *planner_inputs(
            reasoning_id,
            (missing,),
            missing=("additional_supporting_observation",),
            limitations=("room_geometry.stereo_speaker_positions", "sbir.best_match"),
        )
    )

    assert tuple(value.test_type for value in synthesis.plans) == (
        EvidenceAcquisitionTestType.ADDITIONAL_OBSERVATION,
        EvidenceAcquisitionTestType.GEOMETRY_ACQUISITION,
    )
    assert all(value.status is EvidenceAcquisitionStatus.READY for value in synthesis.plans)
    assert "speaker_boundary_distance_m" in synthesis.plans[1].measurements_to_capture


def test_no_blocking_factor_produces_no_plan():
    synthesis = EvidenceAcquisitionPlanner().plan(
        *planner_inputs(factors=(), applicability=WeightedActionApplicability.APPLICABLE)
    )
    assert synthesis.plans == ()


def test_planning_does_not_mutate_existing_corrective_action_or_weight():
    reasonings, actions, weights = contradiction_inputs()
    action_before = dict(actions.actions[0].__dict__)
    weight_before = dict(weights.weights[0].__dict__)

    EvidenceAcquisitionPlanner().plan(reasonings, actions, weights)

    assert actions.actions[0].__dict__ == action_before
    assert weights.weights[0].__dict__ == weight_before


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("blocking_factor_ids", (), "blocking factor"),
        ("instructions", (), "instructions"),
        ("success_criteria", (), "success criteria"),
        ("test_type", "UNKNOWN", "enum"),
    ),
)
def test_plan_rejects_incomplete_or_unknown_contract(field, value, message):
    with pytest.raises(ValueError, match=message):
        valid_plan(**{field: value})


def test_planner_rejects_unknown_action_and_reasoning_references():
    reasonings, actions, weights = contradiction_inputs()
    bad_action = replace_namespace(weights.weights[0], action_references=("UNKNOWN",))
    with pytest.raises(ValueError, match="Unknown corrective action"):
        EvidenceAcquisitionPlanner().plan(reasonings, actions, SimpleNamespace(weights=(bad_action,)))
    bad_reasoning = replace_namespace(weights.weights[0], reasoning_references=("UNKNOWN",))
    with pytest.raises(ValueError, match="Unknown reasoning"):
        EvidenceAcquisitionPlanner().plan(reasonings, actions, SimpleNamespace(weights=(bad_reasoning,)))


def replace_namespace(value, **changes):
    data = dict(value.__dict__)
    data.update(changes)
    return SimpleNamespace(**data)


def test_permanent_correction_language_is_rejected():
    with pytest.raises(ValueError, match="permanent correction"):
        valid_plan(instructions=("Move the speaker permanently.",))


def test_controlled_displacement_requires_reversible_protocol_language():
    with pytest.raises(ValueError, match="reversible"):
        valid_plan(test_type=EvidenceAcquisitionTestType.CONTROLLED_SPEAKER_DISPLACEMENT)
    plan = valid_plan(
        test_type=EvidenceAcquisitionTestType.CONTROLLED_SPEAKER_DISPLACEMENT,
        instructions=(
            "Use a protocol-defined temporary displacement, measure before and after, then return to the initial position.",
        ),
        independent_variables=("speaker_position",),
    )
    assert plan.test_type is EvidenceAcquisitionTestType.CONTROLLED_SPEAKER_DISPLACEMENT


def test_presented_json_is_byte_stable_and_ordered():
    synthesis = EvidenceAcquisitionPlanSynthesis((valid_plan(),))
    context = SimpleNamespace(evidence_acquisition_plan_synthesis=synthesis)
    report = EvidenceAcquisitionPlanPresenter().present(context)
    assert report.to_json() == EvidenceAcquisitionPlanPresenter().present(context).to_json()
    assert json.loads(report.to_json())["plans"][0]["plan_id"] == valid_plan().plan_id


def test_advisor_can_reference_only_existing_plans_without_changing_historical_default():
    plan = valid_plan()
    presented = PresentedEvidenceAcquisitionPlan(**{
        key: value for key, value in EvidenceAcquisitionPlanPresenter().present(
            SimpleNamespace(evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis((plan,)))
        ).plans[0].__dict__.items()
    })
    report = Report(project_name="campaign")
    report.evidence_acquisition_plans = PresentedEvidenceAcquisitionPlanReport((presented,))
    context = AdvisorContextBuilder().build(report)
    assert tuple(value.object_id for value in context.objects) == (plan.plan_id,)

    response = AdvisorService().advise(
        report,
        question="Quel test ensuite ?",
        audience=AdvisorAudience.GENERAL,
        detail_level=AdvisorDetailLevel.STANDARD,
        provider=MockAdvisorProvider(),
    )
    assert response.validation_status is AdvisorValidationStatus.VALID
    assert plan.plan_id in response.answer_text
    assert "ne rendent aucune action corrective bloquée applicable" in response.answer_text


def test_mock_advisor_plan_explanations_are_stable_in_french_and_english():
    plan = valid_plan()
    context = SimpleNamespace(
        evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis((plan,))
    )
    report = Report(project_name="campaign")
    report.evidence_acquisition_plans = EvidenceAcquisitionPlanPresenter().present(context)
    service = AdvisorService()
    provider = MockAdvisorProvider()

    french = service.advise(
        report,
        question="Quel test faut-il effectuer ensuite ?",
        audience=AdvisorAudience.GENERAL,
        detail_level=AdvisorDetailLevel.STANDARD,
        provider=provider,
    )
    english = service.advise(
        report,
        question="Which test should be performed next?",
        audience=AdvisorAudience.GENERAL,
        detail_level=AdvisorDetailLevel.STANDARD,
        provider=provider,
    )

    assert french.answer_text.startswith("Les prochains plans déterministes")
    assert english.answer_text.startswith("The next deterministic evidence")
    assert service.advise(
        report,
        question="Quel test faut-il effectuer ensuite ?",
        audience=AdvisorAudience.GENERAL,
        detail_level=AdvisorDetailLevel.STANDARD,
        provider=provider,
    ) == french
