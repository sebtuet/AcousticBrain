import json
from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
from types import SimpleNamespace

import pytest

from acousticbrain.advisor import AdvisorContextBuilder, AdvisorService, MockAdvisorProvider
from acousticbrain.analysis import EvidenceAcquisitionPlanner
from acousticbrain.models import (
    AdvisorAudience,
    AdvisorDetailLevel,
    AdvisorValidationStatus,
    ChannelIsolationCriterionOperator,
    ChannelIsolationEvaluationCriterion,
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
    EvidenceAcquisitionPlanConsoleReporter,
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


def test_presented_plan_preserves_structured_channel_isolation_criteria():
    criterion = ChannelIsolationEvaluationCriterion(
        criterion_id="criterion.channel_balance",
        result_id="result.channel_balance_db",
        operator=ChannelIsolationCriterionOperator.WITHIN_TOLERANCE,
        expected_value=Decimal("0.0"),
        unit="dB",
        tolerance=Decimal("0.5"),
    )
    plan = valid_plan(
        test_type=EvidenceAcquisitionTestType.CHANNEL_ISOLATION,
        channel_isolation_evaluation_criteria=(criterion,),
    )

    presented = EvidenceAcquisitionPlanPresenter().present(
        SimpleNamespace(
            evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis(
                (plan,)
            )
        )
    ).recommended_plan

    assert presented.to_dict()["channel_isolation_evaluation_criteria"] == (
        {
            "criterion_id": "criterion.channel_balance",
            "result_id": "result.channel_balance_db",
            "operator": "WITHIN_TOLERANCE",
            "expected_value": "0.0",
            "unit": "dB",
            "tolerance": "0.5",
        },
    )


def test_display_objective_preserves_structured_source_and_traceability():
    source_objective = (
        "Acquire repeatable evidence for contradiction "
        "reasoning.internal.technical_identifier."
    )
    plan = valid_plan(
        objective=source_objective,
        test_type=EvidenceAcquisitionTestType.CHANNEL_ISOLATION,
        independent_variables=("active_channel",),
        expected_observations=("channel_specific_metric", "repeatability_metric"),
    )
    presented = EvidenceAcquisitionPlanPresenter().present(
        SimpleNamespace(
            evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis(
                (plan,)
            )
        )
    ).recommended_plan
    serialized = presented.to_dict()

    assert presented.display_objective == (
        "Determine whether the observed left/right acoustic difference "
        "is stable and repeatable."
    )
    assert "reasoning." not in presented.display_objective
    assert "caus" not in presented.display_objective.casefold()
    assert serialized["objective"] == source_objective
    assert serialized["reasoning_id"] == plan.reasoning_id
    assert serialized["plan_id"] == plan.plan_id


def test_display_objective_supports_another_existing_test_type():
    plan = valid_plan(
        test_type=EvidenceAcquisitionTestType.COMPARATIVE_MEASUREMENT,
        independent_variables=("active_speaker", "microphone_position"),
        expected_observations=("spatial_change_pattern", "source_tied_pattern"),
    )

    presented = EvidenceAcquisitionPlanPresenter().present(
        SimpleNamespace(
            evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis(
                (plan,)
            )
        )
    ).recommended_plan

    assert presented.display_objective == (
        "Compare the declared experimental variables to determine whether "
        "the expected acoustic patterns differ."
    )


def test_display_objective_has_an_honest_deterministic_fallback():
    plan = valid_plan(
        objective="Technical source objective reasoning.internal.id.",
        test_type=EvidenceAcquisitionTestType.CONTROLLED_MICROPHONE_DISPLACEMENT,
        independent_variables=(),
        expected_observations=(),
    )
    context = SimpleNamespace(
        evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis(
            (plan,)
        )
    )

    first = EvidenceAcquisitionPlanPresenter().present(
        context
    ).recommended_plan.display_objective
    second = EvidenceAcquisitionPlanPresenter().present(
        context
    ).recommended_plan.display_objective

    assert first == second
    assert first == (
        "Acquire the evidence required by the associated acoustic reasoning "
        "without establishing causality."
    )
    assert plan.reasoning_id not in first
    assert "reasoning.internal.id" not in first


def test_single_ready_plan_is_the_recommended_experiment():
    plan = valid_plan()
    report = EvidenceAcquisitionPlanPresenter().present(
        SimpleNamespace(
            evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis((plan,))
        )
    )

    assert report.recommendation_status == "RECOMMENDED_EXPERIMENT"
    assert report.recommended_plan.plan_id == plan.plan_id


def test_multiple_ready_plans_use_priority_then_effort_then_stable_id():
    low_priority = valid_plan(
        plan_id="PLAN_A",
        priority=EvidenceAcquisitionPriority.LOW,
        estimated_effort=EvidenceAcquisitionEffort.LOW,
    )
    high_effort = valid_plan(
        plan_id="PLAN_B",
        priority=EvidenceAcquisitionPriority.HIGH,
        estimated_effort=EvidenceAcquisitionEffort.HIGH,
    )
    expected = valid_plan(
        plan_id="PLAN_C",
        priority=EvidenceAcquisitionPriority.HIGH,
        estimated_effort=EvidenceAcquisitionEffort.LOW,
    )

    def selected(plans):
        return EvidenceAcquisitionPlanPresenter().present(
            SimpleNamespace(
                evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis(plans)
            )
        ).recommended_plan.plan_id

    assert selected((low_priority, high_effort, expected)) == expected.plan_id
    assert selected((expected, low_priority, high_effort)) == expected.plan_id


def test_plan_id_breaks_equal_ready_plan_ranks_independently_of_input_order():
    first = valid_plan(plan_id="PLAN_A")
    second = valid_plan(plan_id="PLAN_B")

    reports = tuple(
        EvidenceAcquisitionPlanPresenter().present(
            SimpleNamespace(
                evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis(plans)
            )
        )
        for plans in ((first, second), (second, first))
    )

    assert tuple(value.recommended_plan.plan_id for value in reports) == (
        "PLAN_A",
        "PLAN_A",
    )
    assert reports[0].selection_justification == reports[1].selection_justification


def test_blocked_plans_and_no_plan_have_distinct_results():
    blocked = valid_plan(status=EvidenceAcquisitionStatus.BLOCKED)
    blocked_report = EvidenceAcquisitionPlanPresenter().present(
        SimpleNamespace(
            evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis((blocked,))
        )
    )
    empty_report = EvidenceAcquisitionPlanPresenter().present(
        SimpleNamespace(
            evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis()
        )
    )

    assert blocked_report.recommendation_status == "ALL_PLANS_BLOCKED"
    assert blocked_report.recommended_plan is None
    assert empty_report.recommendation_status == "NO_PLANS"
    assert empty_report.recommended_plan is None


def test_proposed_and_mixed_non_ready_plans_are_not_reported_as_all_blocked():
    proposed = valid_plan(
        plan_id="PLAN_PROPOSED",
        status=EvidenceAcquisitionStatus.PROPOSED,
    )
    blocked = valid_plan(
        plan_id="PLAN_BLOCKED",
        status=EvidenceAcquisitionStatus.BLOCKED,
    )

    for plans in ((proposed,), (blocked, proposed)):
        report = EvidenceAcquisitionPlanPresenter().present(
            SimpleNamespace(
                evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis(
                    plans
                )
            )
        )
        assert report.recommendation_status == "PLANS_PROPOSED_BUT_NOT_READY"
        assert report.recommended_plan is None


def presentation_context(plan, *, protocols=(), reasoning=None):
    action = SimpleNamespace(
        action_id=plan.corrective_action_id,
        compatible_protocol_ids=tuple(protocols),
    )
    values = {
        "evidence_acquisition_plan_synthesis": EvidenceAcquisitionPlanSynthesis(
            (plan,)
        ),
        "deterministic_corrective_action_synthesis": SimpleNamespace(
            actions=(action,)
        ),
    }
    if reasoning is not None:
        values["deterministic_acoustic_reasoning_synthesis"] = SimpleNamespace(
            reasonings=(reasoning,)
        )
    return SimpleNamespace(**values)


def test_protocol_projection_uses_exact_source_action_and_stable_order():
    plan = valid_plan()
    context = presentation_context(
        plan,
        protocols=("protocol.z", "VERIFY_SPEAKER_ROOM_ASYMMETRY", "protocol.a"),
    )

    first = EvidenceAcquisitionPlanPresenter().present(context).recommended_plan
    second = EvidenceAcquisitionPlanPresenter().present(context).recommended_plan

    assert first.corrective_action_id == plan.corrective_action_id
    assert first.compatible_protocol_ids == (
        "VERIFY_SPEAKER_ROOM_ASYMMETRY",
        "protocol.a",
        "protocol.z",
    )
    assert second.compatible_protocol_ids == first.compatible_protocol_ids


def test_protocol_projection_does_not_guess_when_source_action_has_none():
    plan = valid_plan()
    presented = EvidenceAcquisitionPlanPresenter().present(
        presentation_context(plan)
    ).recommended_plan

    assert presented.compatible_protocol_ids == ()


def test_protocol_projection_does_not_leak_from_an_unrelated_action():
    plan = valid_plan()
    context = SimpleNamespace(
        evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis(
            (plan,)
        ),
        deterministic_corrective_action_synthesis=SimpleNamespace(
            actions=(
                SimpleNamespace(
                    action_id="UNRELATED_ACTION",
                    compatible_protocol_ids=("UNRELATED_PROTOCOL",),
                ),
            )
        ),
    )

    presented = EvidenceAcquisitionPlanPresenter().present(
        context
    ).recommended_plan

    assert presented.compatible_protocol_ids == ()


def test_required_input_availability_is_not_invented():
    required = EvidenceAcquisitionPlanPresenter().present(
        presentation_context(valid_plan())
    ).recommended_plan
    not_required = EvidenceAcquisitionPlanPresenter().present(
        presentation_context(valid_plan(required_inputs=()))
    ).recommended_plan

    assert required.prerequisite_status == "AVAILABILITY_NOT_VERIFIED"
    assert not_required.prerequisite_status == "NO_REQUIRED_INPUTS"


def test_scientific_justification_is_distinct_from_selection_rationale():
    plan = valid_plan(
        test_type=EvidenceAcquisitionTestType.CHANNEL_ISOLATION,
        expected_observations=("channel_difference", "repeatability"),
        limitations=("The plan does not establish the cause.",),
    )
    reasoning = SimpleNamespace(
        reasoning_id=plan.reasoning_id,
        title="Existing hypothesis explanation: SPEAKER_ROOM_ASYMMETRY",
        conclusion=SimpleNamespace(value="NON_DISCRIMINATED"),
        observation_ids=("OBSERVATION_LEFT_RIGHT", "OBSERVATION_ETC"),
        premises=(
            SimpleNamespace(
                source_type=SimpleNamespace(value="OBSERVATION"),
                role=SimpleNamespace(value="SUPPORTING"),
            ),
            SimpleNamespace(
                source_type=SimpleNamespace(value="OBSERVATION"),
                role=SimpleNamespace(value="SUPPORTING"),
            ),
        ),
        contradicting_evidence=("INTERNAL_CONTRADICTION_ID",),
    )
    report = EvidenceAcquisitionPlanPresenter().present(
        presentation_context(plan, reasoning=reasoning)
    )

    assert "2 structured observations" in report.recommended_plan.scientific_justification
    assert "speaker room asymmetry" in report.recommended_plan.scientific_justification
    assert "retains contradictory evidence" in report.recommended_plan.scientific_justification
    assert "LEFT and RIGHT separately" in report.recommended_plan.scientific_justification
    assert "stable and repeatable" in report.recommended_plan.scientific_justification
    assert "does not establish causality" in report.recommended_plan.scientific_justification
    assert plan.reasoning_id not in report.recommended_plan.scientific_justification
    assert "INTERNAL_CONTRADICTION_ID" not in report.recommended_plan.scientific_justification
    assert "priority" not in report.recommended_plan.scientific_justification
    assert "priority" in report.selection_justification


def test_recommended_output_preserves_fields_and_does_not_invent_protocol_parameters():
    limitation = "No distance, position, repetition or acquisition parameter is known."
    plan = valid_plan(
        limitations=(limitation,),
        instructions=("Use only the already documented acquisition settings.",),
    )
    report = Report(project_name="campaign")
    report.evidence_acquisition_plans = EvidenceAcquisitionPlanPresenter().present(
        SimpleNamespace(
            evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis((plan,))
        )
    )
    output = StringIO()

    with redirect_stdout(output):
        EvidenceAcquisitionPlanConsoleReporter().print(report)

    rendered = output.getvalue()
    for label in (
        "Objective",
        "Why This Experiment",
        "Protocol",
        "Required Inputs",
        "Prerequisite Availability",
        "Procedure",
        "Keep Constant",
        "Variables Under Test",
        "Measurements",
        "Expected Observations",
        "Success Criteria",
        "Failure Criteria",
        "Limitations",
        "Selection Rationale",
    ):
        assert label in rendered
    assert "- not specified" in rendered
    assert "Not verified by the evidence acquisition plan" in rendered
    assert limitation in rendered
    assert " cm" not in rendered


def test_console_uses_display_objective_without_exposing_source_identifier():
    source_identifier = "reasoning.internal.technical_identifier"
    plan = valid_plan(
        objective=f"Acquire evidence for contradiction {source_identifier}.",
        test_type=EvidenceAcquisitionTestType.CHANNEL_ISOLATION,
        independent_variables=("active_channel",),
        expected_observations=("channel_specific_metric", "repeatability_metric"),
    )
    report = Report(project_name="campaign")
    report.evidence_acquisition_plans = EvidenceAcquisitionPlanPresenter().present(
        SimpleNamespace(
            evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis(
                (plan,)
            )
        )
    )
    output = StringIO()

    with redirect_stdout(output):
        EvidenceAcquisitionPlanConsoleReporter().print(report)

    rendered = output.getvalue()
    objective = rendered.split("Objective\n", 1)[1].split("\n\n", 1)[0]
    assert objective == (
        "Determine whether the observed left/right acoustic difference "
        "is stable and repeatable."
    )
    assert source_identifier not in objective


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
