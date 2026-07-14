from dataclasses import dataclass
from enum import Enum
from math import isfinite


class ReflectionExperimentComparisonStatus(Enum):
    NOT_COMPARABLE = "NOT_COMPARABLE"
    NO_OBSERVABLE_CHANGE = "NO_OBSERVABLE_CHANGE"
    CHANGE_OBSERVED = "CHANGE_OBSERVED"
    INCONCLUSIVE = "INCONCLUSIVE"


class ReflectionComparisonCausalityStatus(Enum):
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class ReflectionComparisonImpact(Enum):
    NONE = "NONE"


@dataclass(frozen=True)
class ReflectionComparisonObservation:
    measurement_reference_id: str
    temporal_window_code: str
    observable_code: str
    value: float
    unit: str
    provenance_codes: tuple[str, ...]

    def __post_init__(self):
        identifiers = (
            self.measurement_reference_id,
            self.temporal_window_code,
            self.observable_code,
            self.unit,
        )
        if any(not isinstance(item, str) or not item.strip() for item in identifiers):
            raise ValueError("Reflection comparison observations require identifiers.")
        if not isinstance(self.value, (int, float)) or isinstance(
            self.value, bool
        ) or not isfinite(self.value):
            raise ValueError("Reflection comparison observations must be finite.")
        if (
            not isinstance(self.provenance_codes, tuple)
            or not self.provenance_codes
            or any(not isinstance(item, str) or not item.strip() for item in self.provenance_codes)
            or len(self.provenance_codes) != len(set(self.provenance_codes))
        ):
            raise ValueError("Observation provenance must be explicit and unique.")


@dataclass(frozen=True)
class ObservedReflectionDifference:
    observable_code: str
    unit: str
    baseline_value: float
    intervention_value: float
    signed_difference: float
    absolute_difference: float
    baseline_provenance_codes: tuple[str, ...]
    intervention_provenance_codes: tuple[str, ...]

    def __post_init__(self):
        if any(
            not isinstance(item, str) or not item.strip()
            for item in (self.observable_code, self.unit)
        ):
            raise ValueError("Observed differences require identifiers.")
        values = (
            self.baseline_value,
            self.intervention_value,
            self.signed_difference,
            self.absolute_difference,
        )
        if any(
            not isinstance(item, (int, float))
            or isinstance(item, bool)
            or not isfinite(item)
            for item in values
        ):
            raise ValueError("Observed differences must be finite.")
        expected = round(self.intervention_value - self.baseline_value, 10)
        if self.signed_difference != expected or self.absolute_difference != abs(expected):
            raise ValueError("Observed differences must be derived arithmetically.")
        for provenance in (
            self.baseline_provenance_codes,
            self.intervention_provenance_codes,
        ):
            if not provenance or any(
                not isinstance(item, str) or not item.strip() for item in provenance
            ):
                raise ValueError("Difference provenance must remain separated.")


@dataclass(frozen=True)
class ControlledReflectionExperimentComparison:
    comparison_id: str
    experiment_declaration_id: str
    proposal_id: str
    status: ReflectionExperimentComparisonStatus
    temporal_window_code: str
    baseline_measurement_reference_ids: tuple[str, ...]
    intervention_measurement_reference_ids: tuple[str, ...]
    observed_differences: tuple[ObservedReflectionDifference, ...]
    reason_codes: tuple[str, ...]
    causality_status: ReflectionComparisonCausalityStatus
    ranking_impact: ReflectionComparisonImpact
    recommendation_impact: ReflectionComparisonImpact
    eligibility_impact: ReflectionComparisonImpact
    source_analysis_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]

    def __post_init__(self):
        identifiers = (
            self.comparison_id,
            self.experiment_declaration_id,
            self.proposal_id,
            self.temporal_window_code,
        )
        if any(not isinstance(item, str) or not item.strip() for item in identifiers):
            raise ValueError("Reflection comparison identifiers are required.")
        if self.comparison_id != f"reflection_experiment_comparison.{self.experiment_declaration_id}":
            raise ValueError("Comparison identifier must derive from declaration id.")
        if not isinstance(self.status, ReflectionExperimentComparisonStatus):
            raise ValueError("Reflection comparison status is invalid.")
        collections = (
            self.baseline_measurement_reference_ids,
            self.intervention_measurement_reference_ids,
            self.reason_codes,
            self.source_analysis_codes,
            self.applied_rule_codes,
        )
        if any(
            not isinstance(values, tuple)
            or any(not isinstance(item, str) or not item.strip() for item in values)
            or len(values) != len(set(values))
            for values in collections
        ):
            raise ValueError("Reflection comparison trace fields must be unique tuples.")
        if not isinstance(self.observed_differences, tuple) or any(
            not isinstance(item, ObservedReflectionDifference)
            for item in self.observed_differences
        ):
            raise ValueError("Observed differences must be a typed tuple.")
        codes = tuple(item.observable_code for item in self.observed_differences)
        if len(codes) != len(set(codes)):
            raise ValueError("Observed differences must be unique per observable.")
        if self.status is ReflectionExperimentComparisonStatus.NO_OBSERVABLE_CHANGE and (
            not self.observed_differences
            or any(item.absolute_difference != 0.0 for item in self.observed_differences)
        ):
            raise ValueError("No-change status requires exact observed equality.")
        if self.status is ReflectionExperimentComparisonStatus.CHANGE_OBSERVED and (
            not self.observed_differences
            or not any(item.absolute_difference > 0.0 for item in self.observed_differences)
        ):
            raise ValueError("Change status requires an observed numerical difference.")
        requires_reasons = self.status in {
            ReflectionExperimentComparisonStatus.NOT_COMPARABLE,
            ReflectionExperimentComparisonStatus.INCONCLUSIVE,
        }
        if requires_reasons != bool(self.reason_codes):
            raise ValueError("Reflection comparison reasons are inconsistent with status.")
        if self.causality_status is not ReflectionComparisonCausalityStatus.NOT_ESTABLISHED:
            raise ValueError("PR-038 cannot establish causality.")
        impacts = (
            self.ranking_impact,
            self.recommendation_impact,
            self.eligibility_impact,
        )
        if any(item is not ReflectionComparisonImpact.NONE for item in impacts):
            raise ValueError("PR-038 cannot affect decisions.")


@dataclass(frozen=True)
class ControlledReflectionExperimentComparisonRegistry:
    comparisons: tuple[ControlledReflectionExperimentComparison, ...]
    schema_version: int = 1

    def __post_init__(self):
        if self.schema_version != 1:
            raise ValueError("Unsupported reflection comparison schema version.")
        if not isinstance(self.comparisons, tuple) or any(
            not isinstance(item, ControlledReflectionExperimentComparison)
            for item in self.comparisons
        ):
            raise ValueError("Reflection comparison registry must be typed.")
        identifiers = tuple(item.comparison_id for item in self.comparisons)
        declarations = tuple(item.experiment_declaration_id for item in self.comparisons)
        if len(identifiers) != len(set(identifiers)) or len(declarations) != len(set(declarations)):
            raise ValueError("Reflection comparisons must be unique per declaration.")
