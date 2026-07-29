from collections import defaultdict
from decimal import localcontext

from acousticbrain.models import (
    ChannelIsolationCriterionEvaluation,
    ChannelIsolationCriterionOperator,
    CriterionEvaluationReason,
    CriterionEvaluationStatus,
    EvidenceAcquisitionTestType,
    PlanResultEvaluation,
    PlanResultEvaluationStatus,
)


class ChannelIsolationPlanResultEvaluator:
    """Evaluates declared results against exact structured plan criteria."""

    _LIMITATION = (
        "Result compatibility applies only to evaluated declared criteria; "
        "it does not validate execution, scientific success, or causality."
    )
    _PARTIAL_LIMITATION = (
        "Some criteria were not evaluable; compatibility is limited to "
        "the criteria that were evaluated."
    )

    def evaluate(self, experiment, resolved_plan):
        if resolved_plan is None:
            return self._result(
                PlanResultEvaluationStatus.NOT_APPLICABLE,
                limitations=(
                    "Result evaluation requires an exactly resolved plan reference.",
                ),
            )
        if (
            getattr(resolved_plan, "test_type", None)
            is not EvidenceAcquisitionTestType.CHANNEL_ISOLATION
        ):
            return self._result(
                PlanResultEvaluationStatus.NOT_APPLICABLE,
                limitations=(
                    "Result evaluation supports CHANNEL_ISOLATION only.",
                ),
            )

        criteria = resolved_plan.channel_isolation_evaluation_criteria
        if not criteria:
            return self._result(
                PlanResultEvaluationStatus.CRITERIA_NOT_EVALUABLE,
                limitations=(
                    "The resolved CHANNEL_ISOLATION plan has no structured "
                    "evaluation criteria.",
                ),
            )

        declaration = experiment.channel_isolation_result_declaration
        results = declaration.measurements if declaration is not None else ()
        results_by_id = defaultdict(list)
        for result in results:
            results_by_id[result.result_id].append(result)

        evaluations = tuple(sorted(
            (
                self._evaluate_criterion(criterion, results_by_id)
                for criterion in criteria
            ),
            key=lambda value: (value.criterion_id, value.result_id),
        ))
        missing_results = {
            value.result_id
            for value in evaluations
            if value.reason_code is CriterionEvaluationReason.RESULT_MISSING
        }
        criterion_result_ids = {
            criterion.result_id for criterion in criteria
        }
        unused_results = {
            result.result_id
            for result in results
            if result.result_id not in criterion_result_ids
        }
        compatible = tuple(
            value
            for value in evaluations
            if value.evaluation_status is CriterionEvaluationStatus.COMPATIBLE
        )
        incompatible = tuple(
            value
            for value in evaluations
            if value.evaluation_status is CriterionEvaluationStatus.INCOMPATIBLE
        )
        unevaluable = tuple(
            value
            for value in evaluations
            if value.evaluation_status is CriterionEvaluationStatus.UNEVALUABLE
        )
        limitations = {self._LIMITATION}
        if compatible and incompatible:
            status = PlanResultEvaluationStatus.MIXED
        elif incompatible:
            status = PlanResultEvaluationStatus.INCOMPATIBLE
        elif compatible:
            status = PlanResultEvaluationStatus.COMPATIBLE
        elif all(
            value.reason_code is CriterionEvaluationReason.RESULT_MISSING
            for value in unevaluable
        ):
            status = PlanResultEvaluationStatus.INSUFFICIENT_EVIDENCE
        else:
            status = PlanResultEvaluationStatus.CRITERIA_NOT_EVALUABLE
        if unevaluable and (compatible or incompatible):
            limitations.add(self._PARTIAL_LIMITATION)
        return self._result(
            status,
            criteria=evaluations,
            missing_results=missing_results,
            unused_results=unused_results,
            limitations=limitations,
        )

    @classmethod
    def _evaluate_criterion(cls, criterion, results_by_id):
        matches = results_by_id.get(criterion.result_id, ())
        if not matches:
            return cls._evaluation(
                criterion,
                CriterionEvaluationStatus.UNEVALUABLE,
                CriterionEvaluationReason.RESULT_MISSING,
            )
        if len(matches) != 1:
            return cls._evaluation(
                criterion,
                CriterionEvaluationStatus.UNEVALUABLE,
                CriterionEvaluationReason.DUPLICATE_RESULT,
            )
        result = matches[0]
        if result.unit is None:
            return cls._evaluation(
                criterion,
                CriterionEvaluationStatus.UNEVALUABLE,
                CriterionEvaluationReason.UNIT_MISSING,
            )
        if result.unit != criterion.unit:
            return cls._evaluation(
                criterion,
                CriterionEvaluationStatus.UNEVALUABLE,
                CriterionEvaluationReason.UNIT_MISMATCH,
            )
        if criterion.operator is ChannelIsolationCriterionOperator.EQUAL:
            compatible = result.value == criterion.expected_value
            reason = (
                CriterionEvaluationReason.VALUE_MATCHES_EXPECTATION
                if compatible
                else CriterionEvaluationReason.VALUE_OUTSIDE_EXPECTATION
            )
        else:
            compatible = cls._within_tolerance(
                result.value,
                criterion.expected_value,
                criterion.tolerance,
            )
            reason = (
                CriterionEvaluationReason.VALUE_WITHIN_EXPECTED_TOLERANCE
                if compatible
                else CriterionEvaluationReason.VALUE_OUTSIDE_EXPECTATION
            )
        return cls._evaluation(
            criterion,
            (
                CriterionEvaluationStatus.COMPATIBLE
                if compatible
                else CriterionEvaluationStatus.INCOMPATIBLE
            ),
            reason,
        )

    @staticmethod
    def _within_tolerance(value, expected, tolerance):
        decimals = (value, expected, tolerance)
        precision = max(
            len(item.as_tuple().digits) + abs(item.as_tuple().exponent)
            for item in decimals
        ) + 10
        with localcontext() as context:
            context.prec = precision
            return abs(value - expected) <= tolerance

    @staticmethod
    def _evaluation(criterion, status, reason):
        return ChannelIsolationCriterionEvaluation(
            criterion_id=criterion.criterion_id,
            result_id=criterion.result_id,
            evaluation_status=status,
            reason_code=reason,
        )

    @staticmethod
    def _result(
        status,
        *,
        criteria=(),
        missing_results=(),
        unused_results=(),
        limitations=(),
    ):
        return PlanResultEvaluation(
            status=status,
            criteria=tuple(criteria),
            missing_results=tuple(sorted(set(missing_results))),
            unused_results=tuple(sorted(set(unused_results))),
            limitations=tuple(sorted(set(limitations))),
        )
