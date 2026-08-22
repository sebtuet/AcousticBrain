"""Pure application qualification of an existing repeatability verdict."""

from dataclasses import dataclass
from enum import Enum

from .channel_isolation_repeatability_evaluation import (
    ChannelIsolationRepeatabilityEvaluation,
    RepeatabilityEvaluationStatus,
)


class ChannelIsolationRepeatabilityQualificationStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    NOT_QUALIFIED = "NOT_QUALIFIED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class ChannelIsolationRepeatabilityMetric:
    maximum_difference_db: float | None
    maximum_difference_frequency_hz: float | None


@dataclass(frozen=True)
class ChannelIsolationRepeatabilityQualificationProvenance:
    experiment_id: str
    capture_labels: tuple[str, str]
    repeatability_contract_id: str
    repeatability_contract_version: str
    lower_hz: float
    upper_hz: float
    threshold_db: float


@dataclass(frozen=True)
class ChannelIsolationRepeatabilityQualification:
    """An immutable suitability projection for a later placement comparison."""

    repeatability_contract_id: str
    repeatability_contract_version: str
    left_channel_metric: ChannelIsolationRepeatabilityMetric
    right_channel_metric: ChannelIsolationRepeatabilityMetric
    source_numeric_verdict: RepeatabilityEvaluationStatus
    qualification_status: ChannelIsolationRepeatabilityQualificationStatus
    reason_codes: tuple[str, ...]
    provenance: ChannelIsolationRepeatabilityQualificationProvenance
    causality_status: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        if tuple(sorted(set(self.reason_codes))) != self.reason_codes:
            raise ValueError("Repeatability qualification reason codes must be canonical.")
        if self.causality_status != "NOT_ESTABLISHED":
            raise ValueError("Repeatability qualification cannot establish causality.")


class ChannelIsolationRepeatabilityQualificationService:
    """Maps an existing numerical verdict without adding an acoustic rule."""

    _STATUS_BY_SOURCE_VERDICT = {
        RepeatabilityEvaluationStatus.REPEATABILITY_ACCEPTABLE_IN_BAND: (
            ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED
        ),
        RepeatabilityEvaluationStatus.REPEATABILITY_UNCERTAIN: (
            ChannelIsolationRepeatabilityQualificationStatus.NOT_QUALIFIED
        ),
        RepeatabilityEvaluationStatus.NOT_EVALUABLE: (
            ChannelIsolationRepeatabilityQualificationStatus.INDETERMINATE
        ),
    }

    def qualify(self, evaluations):
        """Preserves the supplied verdict and maps only its existing meaning."""
        return tuple(
            self._qualify(evaluation)
            for evaluation in sorted(evaluations, key=lambda item: item.experiment_id)
        )

    def _qualify(self, evaluation: ChannelIsolationRepeatabilityEvaluation):
        source_verdict = evaluation.status
        return ChannelIsolationRepeatabilityQualification(
            repeatability_contract_id=evaluation.contract_id,
            repeatability_contract_version=evaluation.contract_version,
            left_channel_metric=ChannelIsolationRepeatabilityMetric(
                maximum_difference_db=evaluation.left_maximum_difference_db,
                maximum_difference_frequency_hz=(
                    evaluation.left_maximum_difference_frequency_hz
                ),
            ),
            right_channel_metric=ChannelIsolationRepeatabilityMetric(
                maximum_difference_db=evaluation.right_maximum_difference_db,
                maximum_difference_frequency_hz=(
                    evaluation.right_maximum_difference_frequency_hz
                ),
            ),
            source_numeric_verdict=source_verdict,
            qualification_status=self._STATUS_BY_SOURCE_VERDICT[source_verdict],
            reason_codes=(source_verdict.value,),
            provenance=ChannelIsolationRepeatabilityQualificationProvenance(
                experiment_id=evaluation.experiment_id,
                capture_labels=evaluation.labels,
                repeatability_contract_id=evaluation.contract_id,
                repeatability_contract_version=evaluation.contract_version,
                lower_hz=evaluation.lower_hz,
                upper_hz=evaluation.upper_hz,
                threshold_db=evaluation.threshold_db,
            ),
        )
