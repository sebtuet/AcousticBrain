from types import SimpleNamespace

import pytest

from acousticbrain.application import (
    PlacementComparisonQualificationService,
    PlacementComparisonStatus,
)
from acousticbrain.models import (
    ComparisonEligibilityStatus,
    ExperimentAcousticOutcome,
    ExperimentFactChange,
    ExperimentFactDelta,
)


def delta(code, change=ExperimentFactChange.IMPROVED):
    return ExperimentFactDelta(
        fact_code=code,
        before=10.0,
        after=8.0,
        delta=-2.0,
        unit="DB",
        change=change,
        threshold=1.0,
        source_analysis_codes=(f"source:{code}",),
    )


def comparison(outcome, *, eligibility=ComparisonEligibilityStatus.COMPARABLE,
               deltas=None, provenance=("measurement:reference", "measurement:target")):
    return SimpleNamespace(
        before_experiment_id="position-a",
        after_experiment_id="position-b",
        result_id="comparison:local:position-a:position-b",
        eligibility=eligibility,
        acoustic_outcome=ExperimentAcousticOutcome(outcome),
        fact_deltas=(delta("metric.a"),) if deltas is None else deltas,
        provenance_codes=provenance,
    )


@pytest.mark.parametrize(
    ("outcome", "status"),
    (
        ("IMPROVED", PlacementComparisonStatus.BETTER),
        ("DEGRADED", PlacementComparisonStatus.WORSE),
        ("UNCHANGED", PlacementComparisonStatus.EQUIVALENT),
        ("MIXED", PlacementComparisonStatus.INDETERMINATE),
        ("INCONCLUSIVE", PlacementComparisonStatus.INDETERMINATE),
    ),
)
def test_projects_only_the_existing_acoustic_outcome(outcome, status):
    source = comparison(outcome)

    result = PlacementComparisonQualificationService().qualify(source)

    assert result.comparison_status is status
    assert result.source_acoustic_outcome is source.acoustic_outcome
    assert result.reason_codes == (outcome,)
    assert result.causality_status == "NOT_ESTABLISHED"


def test_preserves_identity_deltas_and_provenance_exactly():
    deltas = (
        delta("metric.b", ExperimentFactChange.DEGRADED),
        delta("metric.a", ExperimentFactChange.IMPROVED),
    )
    source = comparison("MIXED", deltas=deltas, provenance=("source.b", "source.a"))

    result = PlacementComparisonQualificationService().qualify(source)

    assert result.reference_experiment_id == "position-a"
    assert result.target_experiment_id == "position-b"
    assert result.source_comparison_result_id == source.result_id
    assert result.supporting_metric_deltas is deltas
    assert result.provenance_codes is source.provenance_codes


def test_mixed_existing_directions_remain_indeterminate_without_aggregation():
    source = comparison(
        "MIXED",
        deltas=(
            delta("metric.b", ExperimentFactChange.DEGRADED),
            delta("metric.a", ExperimentFactChange.IMPROVED),
        ),
    )

    result = PlacementComparisonQualificationService().qualify(source)

    assert result.comparison_status is PlacementComparisonStatus.INDETERMINATE
    assert result.reason_codes == ("MIXED",)


def test_non_comparable_result_cannot_reach_placement_qualification():
    source = comparison(
        "INCONCLUSIVE", eligibility=ComparisonEligibilityStatus.NOT_COMPARABLE
    )
    before = (
        source.before_experiment_id,
        source.after_experiment_id,
        source.fact_deltas,
        source.provenance_codes,
    )

    with pytest.raises(ValueError, match="Only comparable experiment results"):
        PlacementComparisonQualificationService().qualify(source)

    assert (
        source.before_experiment_id,
        source.after_experiment_id,
        source.fact_deltas,
        source.provenance_codes,
    ) == before


def test_status_does_not_depend_on_metric_collection_order():
    first = comparison(
        "MIXED",
        deltas=(
            delta("metric.a", ExperimentFactChange.IMPROVED),
            delta("metric.b", ExperimentFactChange.DEGRADED),
        ),
    )
    second = comparison(
        "MIXED",
        deltas=tuple(reversed(first.fact_deltas)),
    )

    service = PlacementComparisonQualificationService()

    assert service.qualify(first).comparison_status is (
        service.qualify(second).comparison_status
    )
