from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ChannelIsolationCriterionOperator(Enum):
    EQUAL = "EQUAL"
    WITHIN_TOLERANCE = "WITHIN_TOLERANCE"


@dataclass(frozen=True)
class ChannelIsolationEvaluationCriterion:
    criterion_id: str
    result_id: str
    operator: ChannelIsolationCriterionOperator
    expected_value: Decimal
    unit: str
    tolerance: Decimal | None = None

    def __post_init__(self):
        if (
            not isinstance(self.criterion_id, str)
            or not self.criterion_id
            or not isinstance(self.result_id, str)
            or not self.result_id
            or not isinstance(self.unit, str)
            or not self.unit
        ):
            raise ValueError(
                "Channel isolation criteria require exact non-empty identifiers."
            )
        if (
            not isinstance(self.expected_value, Decimal)
            or not self.expected_value.is_finite()
        ):
            raise ValueError(
                "Channel isolation criterion values must be finite decimals."
            )
        if not isinstance(self.operator, ChannelIsolationCriterionOperator):
            raise ValueError("Unsupported channel isolation criterion operator.")
        if self.operator is ChannelIsolationCriterionOperator.EQUAL:
            if self.tolerance is not None:
                raise ValueError("EQUAL criteria cannot declare a tolerance.")
        elif (
            not isinstance(self.tolerance, Decimal)
            or not self.tolerance.is_finite()
            or self.tolerance < 0
        ):
            raise ValueError(
                "WITHIN_TOLERANCE criteria require a non-negative finite tolerance."
            )

    def to_dict(self):
        return {
            "criterion_id": self.criterion_id,
            "result_id": self.result_id,
            "operator": self.operator.value,
            "expected_value": str(self.expected_value),
            "unit": self.unit,
            "tolerance": (
                str(self.tolerance)
                if self.tolerance is not None
                else None
            ),
        }


@dataclass(frozen=True)
class ChannelIsolationMeasurementResult:
    result_id: str
    value: Decimal
    unit: str | None

    def __post_init__(self):
        if not isinstance(self.result_id, str) or not self.result_id:
            raise ValueError(
                "Channel isolation results require an exact non-empty identifier."
            )
        if not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise ValueError(
                "Channel isolation result values must be finite decimals."
            )
        if self.unit is not None and (
            not isinstance(self.unit, str) or not self.unit
        ):
            raise ValueError(
                "Channel isolation result units must be absent or non-empty."
            )


@dataclass(frozen=True)
class ChannelIsolationResultDeclaration:
    measurements: tuple[ChannelIsolationMeasurementResult, ...]

    def __post_init__(self):
        if not isinstance(self.measurements, tuple) or any(
            not isinstance(value, ChannelIsolationMeasurementResult)
            for value in self.measurements
        ):
            raise ValueError(
                "Channel isolation result declarations require typed measurements."
            )


class PlanResultEvaluationStatus(Enum):
    NOT_APPLICABLE = "PLAN_RESULT_NOT_APPLICABLE"
    INSUFFICIENT_EVIDENCE = "PLAN_RESULT_INSUFFICIENT_EVIDENCE"
    CRITERIA_NOT_EVALUABLE = "PLAN_RESULT_CRITERIA_NOT_EVALUABLE"
    COMPATIBLE = "PLAN_RESULT_COMPATIBLE"
    INCOMPATIBLE = "PLAN_RESULT_INCOMPATIBLE"
    MIXED = "PLAN_RESULT_MIXED"


class CriterionEvaluationStatus(Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNEVALUABLE = "UNEVALUABLE"


class CriterionEvaluationReason(Enum):
    RESULT_MISSING = "RESULT_MISSING"
    UNIT_MISSING = "UNIT_MISSING"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    DUPLICATE_RESULT = "DUPLICATE_RESULT"
    VALUE_MATCHES_EXPECTATION = "VALUE_MATCHES_EXPECTATION"
    VALUE_WITHIN_EXPECTED_TOLERANCE = "VALUE_WITHIN_EXPECTED_TOLERANCE"
    VALUE_OUTSIDE_EXPECTATION = "VALUE_OUTSIDE_EXPECTATION"


@dataclass(frozen=True)
class ChannelIsolationCriterionEvaluation:
    criterion_id: str
    result_id: str
    evaluation_status: CriterionEvaluationStatus
    reason_code: CriterionEvaluationReason

    def __post_init__(self):
        if not self.criterion_id or not self.result_id:
            raise ValueError("Criterion evaluation identifiers are required.")
        if not isinstance(self.evaluation_status, CriterionEvaluationStatus):
            raise ValueError("Criterion evaluation status is invalid.")
        if not isinstance(self.reason_code, CriterionEvaluationReason):
            raise ValueError("Criterion evaluation reason is invalid.")


@dataclass(frozen=True)
class PlanResultEvaluation:
    status: PlanResultEvaluationStatus
    criteria: tuple[ChannelIsolationCriterionEvaluation, ...] = ()
    missing_results: tuple[str, ...] = ()
    unused_results: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.status, PlanResultEvaluationStatus):
            raise ValueError("Plan result evaluation status is invalid.")
        if not isinstance(self.criteria, tuple) or any(
            not isinstance(value, ChannelIsolationCriterionEvaluation)
            for value in self.criteria
        ):
            raise ValueError("Plan result criteria must be typed and immutable.")
        if self.criteria != tuple(sorted(
            self.criteria,
            key=lambda value: (value.criterion_id, value.result_id),
        )):
            raise ValueError("Plan result criteria must be deterministically sorted.")
        for values in (
            self.missing_results,
            self.unused_results,
            self.limitations,
        ):
            if (
                not isinstance(values, tuple)
                or values != tuple(sorted(set(values)))
                or any(not isinstance(value, str) or not value for value in values)
            ):
                raise ValueError(
                    "Plan result evaluation collections must be sorted unique strings."
                )
