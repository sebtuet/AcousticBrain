"""Product-facing projection of an already comparable placement result."""

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from acousticbrain.models import (
    ComparisonEligibilityStatus,
    ExperimentAcousticOutcome,
    ExperimentFactDelta,
)


class PlacementComparisonStatus(str, Enum):
    BETTER = "BETTER"
    WORSE = "WORSE"
    EQUIVALENT = "EQUIVALENT"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class PlacementComparisonQualification:
    """A non-causal reading of the existing acoustic comparison outcome."""

    reference_experiment_id: str
    target_experiment_id: str
    source_comparison_result_id: str
    comparison_status: PlacementComparisonStatus
    source_acoustic_outcome: ExperimentAcousticOutcome
    supporting_metric_deltas: tuple[ExperimentFactDelta, ...]
    reason_codes: tuple[str, ...]
    provenance_codes: tuple[str, ...]
    causality_status: str = "NOT_ESTABLISHED"

    _STATUS_BY_OUTCOME: ClassVar[dict[ExperimentAcousticOutcome, PlacementComparisonStatus]] = {
        ExperimentAcousticOutcome.IMPROVED: PlacementComparisonStatus.BETTER,
        ExperimentAcousticOutcome.DEGRADED: PlacementComparisonStatus.WORSE,
        ExperimentAcousticOutcome.UNCHANGED: PlacementComparisonStatus.EQUIVALENT,
        ExperimentAcousticOutcome.MIXED: PlacementComparisonStatus.INDETERMINATE,
        ExperimentAcousticOutcome.INCONCLUSIVE: (
            PlacementComparisonStatus.INDETERMINATE
        ),
    }

    def __post_init__(self):
        if any(not isinstance(value, str) or not value for value in (
            self.reference_experiment_id,
            self.target_experiment_id,
            self.source_comparison_result_id,
        )):
            raise ValueError("Placement comparison identities are required.")
        if not isinstance(self.comparison_status, PlacementComparisonStatus):
            raise ValueError("Placement comparison requires a valid status.")
        if not isinstance(self.source_acoustic_outcome, ExperimentAcousticOutcome):
            raise ValueError("Placement comparison requires its source outcome.")
        if self.comparison_status is not self.status_for(
            self.source_acoustic_outcome
        ):
            raise ValueError(
                "Placement comparison status must preserve its source outcome."
            )
        if not all(isinstance(item, ExperimentFactDelta)
                   for item in self.supporting_metric_deltas):
            raise ValueError("Placement comparison deltas must be preserved.")
        if not isinstance(self.reason_codes, tuple):
            raise ValueError("Placement comparison reason codes must be a tuple.")
        if self.reason_codes != (self.source_acoustic_outcome.value,):
            raise ValueError(
                "Placement comparison reason codes must preserve its source outcome."
            )
        if not isinstance(self.provenance_codes, tuple):
            raise ValueError("Placement comparison provenance must be a tuple.")
        if self.causality_status != "NOT_ESTABLISHED":
            raise ValueError("Placement comparison cannot establish causality.")

    @classmethod
    def status_for(cls, outcome):
        return cls._STATUS_BY_OUTCOME[outcome]


class PlacementComparisonQualificationService:
    """Projects an existing outcome; it does not evaluate acoustic facts."""

    def qualify(self, comparison):
        if comparison.eligibility is not ComparisonEligibilityStatus.COMPARABLE:
            raise ValueError(
                "Only comparable experiment results can qualify a placement comparison."
            )
        outcome = comparison.acoustic_outcome
        return PlacementComparisonQualification(
            reference_experiment_id=comparison.before_experiment_id,
            target_experiment_id=comparison.after_experiment_id,
            source_comparison_result_id=comparison.result_id,
            comparison_status=PlacementComparisonQualification.status_for(outcome),
            source_acoustic_outcome=outcome,
            supporting_metric_deltas=comparison.fact_deltas,
            reason_codes=(outcome.value,),
            provenance_codes=comparison.provenance_codes,
        )
