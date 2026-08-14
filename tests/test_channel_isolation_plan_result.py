from decimal import Decimal

import pytest

from acousticbrain.application import ChannelIsolationPlanResultEvaluator
from acousticbrain.models import (
    ChannelIsolationCriterionOperator,
    ChannelIsolationEvaluationCriterion,
    ChannelIsolationMeasurementResult,
    ChannelIsolationResultDeclaration,
    CriterionEvaluationReason,
    CriterionEvaluationStatus,
    EvidenceAcquisitionEffort,
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionPriority,
    EvidenceAcquisitionStatus,
    EvidenceAcquisitionTestType,
    ExperimentDescriptor,
    ExperimentState,
    ExperimentType,
    PlanResultEvaluationStatus,
)


def criterion(
    criterion_id,
    result_id,
    *,
    operator=ChannelIsolationCriterionOperator.EQUAL,
    expected_value="0",
    unit="dB",
    tolerance=None,
):
    return ChannelIsolationEvaluationCriterion(
        criterion_id=criterion_id,
        result_id=result_id,
        operator=operator,
        expected_value=Decimal(expected_value),
        unit=unit,
        tolerance=Decimal(tolerance) if tolerance is not None else None,
    )


def plan(*criteria, test_type=EvidenceAcquisitionTestType.CHANNEL_ISOLATION):
    return EvidenceAcquisitionPlan(
        plan_id="PLAN",
        reasoning_id="REASONING",
        corrective_action_id="ACTION",
        evidence_weight_id="WEIGHT",
        blocking_factor_ids=("FACTOR",),
        objective="Evaluate declared results.",
        test_type=test_type,
        instructions=("Use the declared protocol.",),
        required_inputs=(),
        controlled_variables=(),
        independent_variables=("active_channel",),
        measurements_to_capture=("metric",),
        expected_observations=("declared_metric",),
        success_criteria=("Use structured criteria only.",),
        failure_criteria=(),
        resulting_evidence_targets=("TARGET",),
        priority=EvidenceAcquisitionPriority.HIGH,
        estimated_effort=EvidenceAcquisitionEffort.MEDIUM,
        status=EvidenceAcquisitionStatus.READY,
        limitations=("No causal conclusion.",),
        channel_isolation_evaluation_criteria=tuple(criteria),
    )


def result(result_id, value, unit="dB"):
    return ChannelIsolationMeasurementResult(
        result_id=result_id,
        value=Decimal(value),
        unit=unit,
    )


def experiment(*results):
    declaration = (
        ChannelIsolationResultDeclaration(tuple(results))
        if results
        else None
    )
    return ExperimentDescriptor(
        experiment_id="exp-001",
        directory="/measurements/exp-001",
        experiment_type=ExperimentType.EXPERIMENT,
        available_files=(),
        available_channels=(),
        wav_files=(),
        txt_files=(),
        mdat_file=None,
        manifest_present=True,
        content_hash="a" * 64,
        timestamp="2026-07-29T10:00:00",
        imported_at="2026-07-29T10:00:00",
        state=ExperimentState.READY,
        channel_isolation_result_declaration=declaration,
    )


def evaluate(experiment_value, plan_value):
    return ChannelIsolationPlanResultEvaluator().evaluate(
        experiment_value,
        plan_value,
    )


def test_result_evaluation_is_not_applicable_without_resolved_plan():
    assert evaluate(experiment(), None).status is (
        PlanResultEvaluationStatus.NOT_APPLICABLE
    )


def test_result_evaluation_is_not_applicable_for_other_plan_type():
    evaluation = evaluate(
        experiment(),
        plan(test_type=EvidenceAcquisitionTestType.REPEAT_MEASUREMENT),
    )

    assert evaluation.status is PlanResultEvaluationStatus.NOT_APPLICABLE
    assert evaluation.limitations == (
        "Result evaluation supports CHANNEL_ISOLATION only.",
    )


def test_unstructured_plan_criteria_are_not_evaluable():
    evaluation = evaluate(experiment(result("metric", "0")), plan())

    assert evaluation.status is (
        PlanResultEvaluationStatus.CRITERIA_NOT_EVALUABLE
    )
    assert evaluation.criteria == ()


def test_structured_criteria_without_results_are_insufficient_evidence():
    evaluation = evaluate(
        experiment(),
        plan(criterion("CRITERION", "metric")),
    )

    assert evaluation.status is (
        PlanResultEvaluationStatus.INSUFFICIENT_EVIDENCE
    )
    assert evaluation.missing_results == ("metric",)
    assert evaluation.criteria[0].reason_code is (
        CriterionEvaluationReason.RESULT_MISSING
    )


@pytest.mark.parametrize(
    ("unit", "reason"),
    (
        (None, CriterionEvaluationReason.UNIT_MISSING),
        ("ratio", CriterionEvaluationReason.UNIT_MISMATCH),
    ),
)
def test_missing_or_different_unit_makes_criterion_unevaluable(unit, reason):
    evaluation = evaluate(
        experiment(result("metric", "0", unit)),
        plan(criterion("CRITERION", "metric")),
    )

    assert evaluation.status is (
        PlanResultEvaluationStatus.CRITERIA_NOT_EVALUABLE
    )
    assert evaluation.criteria[0].evaluation_status is (
        CriterionEvaluationStatus.UNEVALUABLE
    )
    assert evaluation.criteria[0].reason_code is reason


def test_all_evaluated_criteria_compatible():
    evaluation = evaluate(
        experiment(result("metric", "-1.25")),
        plan(criterion(
            "CRITERION",
            "metric",
            expected_value="-1.25",
        )),
    )

    assert evaluation.status is PlanResultEvaluationStatus.COMPATIBLE
    assert evaluation.criteria[0].reason_code is (
        CriterionEvaluationReason.VALUE_MATCHES_EXPECTATION
    )


def test_only_incompatible_criteria_produce_incompatible_status():
    evaluation = evaluate(
        experiment(result("metric", "1")),
        plan(criterion("CRITERION", "metric", expected_value="0")),
    )

    assert evaluation.status is PlanResultEvaluationStatus.INCOMPATIBLE
    assert evaluation.criteria[0].reason_code is (
        CriterionEvaluationReason.VALUE_OUTSIDE_EXPECTATION
    )


def test_compatible_and_incompatible_criteria_produce_mixed_status():
    evaluation = evaluate(
        experiment(
            result("left_metric", "0"),
            result("right_metric", "2"),
        ),
        plan(
            criterion("LEFT", "left_metric"),
            criterion("RIGHT", "right_metric"),
        ),
    )

    assert evaluation.status is PlanResultEvaluationStatus.MIXED


@pytest.mark.parametrize(
    ("value", "expected_status"),
    (
        ("-1", CriterionEvaluationStatus.COMPATIBLE),
        ("0", CriterionEvaluationStatus.COMPATIBLE),
        ("1", CriterionEvaluationStatus.COMPATIBLE),
        ("1.0000000000000000000000000001", CriterionEvaluationStatus.INCOMPATIBLE),
    ),
)
def test_within_tolerance_is_inclusive_and_decimal_exact(value, expected_status):
    evaluation = evaluate(
        experiment(result("metric", value)),
        plan(criterion(
            "CRITERION",
            "metric",
            operator=ChannelIsolationCriterionOperator.WITHIN_TOLERANCE,
            expected_value="0",
            tolerance="1",
        )),
    )

    assert evaluation.criteria[0].evaluation_status is expected_status


def test_equal_has_no_implicit_tolerance():
    evaluation = evaluate(
        experiment(result("metric", "0.0000000000000000001")),
        plan(criterion("CRITERION", "metric", expected_value="0")),
    )

    assert evaluation.status is PlanResultEvaluationStatus.INCOMPATIBLE


def test_duplicate_results_are_never_selected_arbitrarily():
    evaluation = evaluate(
        experiment(
            result("metric", "0"),
            result("metric", "0"),
        ),
        plan(criterion("CRITERION", "metric")),
    )

    assert evaluation.status is (
        PlanResultEvaluationStatus.CRITERIA_NOT_EVALUABLE
    )
    assert evaluation.criteria[0].reason_code is (
        CriterionEvaluationReason.DUPLICATE_RESULT
    )


def test_result_identifiers_use_exact_matching_only():
    evaluation = evaluate(
        experiment(
            result("Left_Response", "0"),
            result("left-response", "0"),
            result("left_response_v2", "0"),
        ),
        plan(criterion("CRITERION", "left_response")),
    )

    assert evaluation.status is (
        PlanResultEvaluationStatus.INSUFFICIENT_EVIDENCE
    )
    assert evaluation.missing_results == ("left_response",)
    assert evaluation.unused_results == (
        "Left_Response",
        "left-response",
        "left_response_v2",
    )


def test_input_order_does_not_change_evaluation():
    criteria = (
        criterion("B", "result_b", expected_value="2"),
        criterion("A", "result_a", expected_value="1"),
    )
    first = evaluate(
        experiment(result("result_b", "2"), result("result_a", "1")),
        plan(*criteria),
    )
    second = evaluate(
        experiment(result("result_a", "1"), result("result_b", "2")),
        plan(*reversed(criteria)),
    )

    assert first == second


def test_compatible_plus_unevaluable_remains_compatible_with_limitation():
    evaluation = evaluate(
        experiment(result("result_a", "1")),
        plan(
            criterion("A", "result_a", expected_value="1"),
            criterion("B", "result_b", expected_value="2"),
        ),
    )

    assert evaluation.status is PlanResultEvaluationStatus.COMPATIBLE
    assert any(
        "Some criteria were not evaluable" in value
        for value in evaluation.limitations
    )


def test_invalid_operator_tolerance_combinations_are_rejected():
    with pytest.raises(ValueError, match="cannot declare a tolerance"):
        criterion("CRITERION", "metric", tolerance="0")
    with pytest.raises(ValueError, match="non-negative"):
        criterion(
            "CRITERION",
            "metric",
            operator=ChannelIsolationCriterionOperator.WITHIN_TOLERANCE,
        )
    with pytest.raises(ValueError, match="non-negative"):
        criterion(
            "CRITERION",
            "metric",
            operator=ChannelIsolationCriterionOperator.WITHIN_TOLERANCE,
            tolerance="-1",
        )
