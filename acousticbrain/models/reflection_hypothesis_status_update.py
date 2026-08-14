from dataclasses import dataclass
from enum import Enum


class ReflectionHypothesisObservationStatus(Enum):
    UNCHANGED = "UNCHANGED"
    INCONCLUSIVE = "INCONCLUSIVE"
    SUPPORTED_BY_OBSERVATION = "SUPPORTED_BY_OBSERVATION"
    NOT_SUPPORTED_BY_OBSERVATION = "NOT_SUPPORTED_BY_OBSERVATION"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"


class ReflectionHypothesisCausalityStatus(Enum):
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class ReflectionHypothesisImpact(Enum):
    NONE = "NONE"


@dataclass(frozen=True)
class ControlledReflectionHypothesisStatusUpdate:
    update_id: str
    target_kind: str
    target_id: str
    proposal_id: str
    experiment_declaration_id: str
    comparison_id: str | None
    status: ReflectionHypothesisObservationStatus
    measured_fact_codes: tuple[str, ...]
    comparison_result_codes: tuple[str, ...]
    transition_rule_codes: tuple[str, ...]
    status_provenance_codes: tuple[str, ...]
    justification_codes: tuple[str, ...]
    causality_status: ReflectionHypothesisCausalityStatus
    recommendation_impact: ReflectionHypothesisImpact
    ranking_impact: ReflectionHypothesisImpact
    eligibility_impact: ReflectionHypothesisImpact
    source_analysis_codes: tuple[str, ...]

    def __post_init__(self):
        required = (
            self.update_id,
            self.target_kind,
            self.target_id,
            self.proposal_id,
            self.experiment_declaration_id,
        )
        if any(not isinstance(item, str) or not item.strip() for item in required):
            raise ValueError("Reflection hypothesis update identifiers are required.")
        if self.target_kind != "CANDIDATE":
            raise ValueError("PR-039 updates observation support for candidates only.")
        expected_source = self.comparison_id or self.experiment_declaration_id
        if self.update_id != f"reflection_hypothesis_status_update.{expected_source}":
            raise ValueError("Hypothesis update identifier must derive from its source.")
        if self.comparison_id is not None and (
            not isinstance(self.comparison_id, str) or not self.comparison_id.strip()
        ):
            raise ValueError("Optional comparison identifiers cannot be empty.")
        if not isinstance(self.status, ReflectionHypothesisObservationStatus):
            raise ValueError("Reflection hypothesis observation status is invalid.")
        collections = (
            self.measured_fact_codes,
            self.comparison_result_codes,
            self.transition_rule_codes,
            self.status_provenance_codes,
            self.justification_codes,
            self.source_analysis_codes,
        )
        if any(
            not isinstance(values, tuple)
            or any(not isinstance(item, str) or not item.strip() for item in values)
            or len(values) != len(set(values))
            for values in collections
        ):
            raise ValueError("Hypothesis update provenance fields must be unique tuples.")
        if not self.transition_rule_codes or not self.status_provenance_codes or not self.justification_codes:
            raise ValueError("Hypothesis status transitions require explicit provenance.")
        if self.comparison_id is None:
            if self.status is not ReflectionHypothesisObservationStatus.NOT_ASSESSABLE:
                raise ValueError("Missing comparisons can only be not assessable.")
            if self.measured_fact_codes or self.comparison_result_codes:
                raise ValueError("Missing comparisons cannot contribute facts or results.")
        if self.status in {
            ReflectionHypothesisObservationStatus.SUPPORTED_BY_OBSERVATION,
            ReflectionHypothesisObservationStatus.NOT_SUPPORTED_BY_OBSERVATION,
        } and not self.comparison_result_codes:
            raise ValueError("Observation support status requires a comparison result.")
        if self.causality_status is not ReflectionHypothesisCausalityStatus.NOT_ESTABLISHED:
            raise ValueError("PR-039 cannot establish causality.")
        impacts = (
            self.recommendation_impact,
            self.ranking_impact,
            self.eligibility_impact,
        )
        if any(item is not ReflectionHypothesisImpact.NONE for item in impacts):
            raise ValueError("PR-039 cannot affect decisions.")


@dataclass(frozen=True)
class ControlledReflectionHypothesisStatusUpdateRegistry:
    updates: tuple[ControlledReflectionHypothesisStatusUpdate, ...]
    schema_version: int = 1

    def __post_init__(self):
        if self.schema_version != 1:
            raise ValueError("Unsupported hypothesis update schema version.")
        if not isinstance(self.updates, tuple) or any(
            not isinstance(item, ControlledReflectionHypothesisStatusUpdate)
            for item in self.updates
        ):
            raise ValueError("Hypothesis update registry must be typed.")
        identifiers = tuple(item.update_id for item in self.updates)
        comparisons = tuple(
            item.comparison_id for item in self.updates if item.comparison_id is not None
        )
        if len(identifiers) != len(set(identifiers)) or len(comparisons) != len(set(comparisons)):
            raise ValueError("Hypothesis updates must be unique per source comparison.")
