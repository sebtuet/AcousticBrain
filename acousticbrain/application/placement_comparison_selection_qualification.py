"""Exact, non-causal orchestration for one selected placement comparison."""

from dataclasses import dataclass

from acousticbrain.models import ComparisonEligibilityStatus

from .channel_isolation_repeatability_qualification import (
    ChannelIsolationRepeatabilityQualification,
)
from .placement_comparison_qualification import (
    PlacementComparisonQualification,
    PlacementComparisonQualificationService,
)


@dataclass(frozen=True)
class PlacementComparisonSelectionQualification:
    """Keeps the selected source, its inputs, and any allowed user verdict."""

    comparison: object
    reference_repeatability_qualification: (
        ChannelIsolationRepeatabilityQualification | None
    )
    target_repeatability_qualification: (
        ChannelIsolationRepeatabilityQualification | None
    )
    placement_qualification: PlacementComparisonQualification | None
    blocking_reason_codes: tuple[str, ...]
    causality_status: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        if self.causality_status != "NOT_ESTABLISHED":
            raise ValueError("Placement selection qualification cannot establish causality.")


class PlacementComparisonSelectionQualificationService:
    """Uses existing identities and services without selecting an alternative."""

    _MISSING_REASON = "REPEATABILITY_QUALIFICATION_MISSING"

    def __init__(self, placement_qualification_service=None):
        self.placement_qualification_service = (
            placement_qualification_service
            or PlacementComparisonQualificationService()
        )

    def qualify(self, comparison_analysis, comparison_id, qualifications):
        comparison = self._comparison(comparison_analysis, comparison_id)
        reference = self._qualification(
            qualifications, comparison.before_experiment_id
        )
        target = self._qualification(qualifications, comparison.after_experiment_id)
        missing = tuple(
            self._MISSING_REASON
            for qualification in (reference, target)
            if qualification is None
        )
        if missing:
            return PlacementComparisonSelectionQualification(
                comparison=comparison,
                reference_repeatability_qualification=reference,
                target_repeatability_qualification=target,
                placement_qualification=None,
                blocking_reason_codes=missing,
            )
        if comparison.eligibility is not ComparisonEligibilityStatus.COMPARABLE:
            return PlacementComparisonSelectionQualification(
                comparison=comparison,
                reference_repeatability_qualification=reference,
                target_repeatability_qualification=target,
                placement_qualification=None,
                blocking_reason_codes=tuple(
                    reason.value for reason in comparison.ineligibility_reasons
                ),
            )
        return PlacementComparisonSelectionQualification(
            comparison=comparison,
            reference_repeatability_qualification=reference,
            target_repeatability_qualification=target,
            placement_qualification=self.placement_qualification_service.qualify(
                comparison
            ),
            blocking_reason_codes=(),
        )

    @staticmethod
    def _comparison(comparison_analysis, comparison_id):
        comparisons = (
            *comparison_analysis.sequence.local_comparisons,
            *comparison_analysis.sequence.cumulative_comparisons,
        )
        matches = tuple(
            item for item in comparisons if item.trace.trace_id == comparison_id
        )
        if not matches:
            raise ValueError(f"COMPARISON_UNKNOWN: {comparison_id}.")
        if len(matches) != 1:
            raise ValueError(f"COMPARISON_AMBIGUOUS: {comparison_id}.")
        return matches[0]

    @classmethod
    def _qualification(cls, qualifications, experiment_id):
        matches = tuple(
            qualification
            for qualification in qualifications
            if cls._qualification_experiment_id(qualification) == experiment_id
        )
        if len(matches) > 1:
            raise ValueError(
                "REPEATABILITY_QUALIFICATION_AMBIGUOUS: "
                f"{experiment_id}."
            )
        return matches[0] if matches else None

    @staticmethod
    def _qualification_experiment_id(qualification):
        if not isinstance(qualification, ChannelIsolationRepeatabilityQualification):
            raise TypeError("Channel-isolation repeatability qualifications are required.")
        return qualification.provenance.experiment_id
