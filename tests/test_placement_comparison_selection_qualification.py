from types import SimpleNamespace

import pytest

from acousticbrain.application import (
    ChannelIsolationRepeatabilityMetric,
    ChannelIsolationRepeatabilityQualification,
    ChannelIsolationRepeatabilityQualificationProvenance,
    ChannelIsolationRepeatabilityQualificationStatus,
    PlacementComparisonSelectionQualificationService,
)
from acousticbrain.application.channel_isolation_repeatability_evaluation import (
    RepeatabilityEvaluationStatus,
)
from acousticbrain.models import (
    ComparisonEligibilityStatus,
    ExperimentAcousticOutcome,
    ExperimentFactChange,
    ExperimentFactDelta,
)


def qualification(experiment_id, status):
    verdict = {
        ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED: (
            RepeatabilityEvaluationStatus.REPEATABILITY_ACCEPTABLE_IN_BAND
        ),
        ChannelIsolationRepeatabilityQualificationStatus.NOT_QUALIFIED: (
            RepeatabilityEvaluationStatus.REPEATABILITY_UNCERTAIN
        ),
        ChannelIsolationRepeatabilityQualificationStatus.INDETERMINATE: (
            RepeatabilityEvaluationStatus.NOT_EVALUABLE
        ),
    }[status]
    return ChannelIsolationRepeatabilityQualification(
        repeatability_contract_id="repeatability_contract.v1",
        repeatability_contract_version="v1",
        left_channel_metric=ChannelIsolationRepeatabilityMetric(0.2, 80.0),
        right_channel_metric=ChannelIsolationRepeatabilityMetric(0.3, 90.0),
        source_numeric_verdict=verdict,
        qualification_status=status,
        reason_codes=(verdict.value,),
        provenance=ChannelIsolationRepeatabilityQualificationProvenance(
            experiment_id=experiment_id,
            capture_labels=("A", "B"),
            repeatability_contract_id="repeatability_contract.v1",
            repeatability_contract_version="v1",
            lower_hz=40.0,
            upper_hz=200.0,
            threshold_db=3.0,
        ),
    )


def comparison(outcome="IMPROVED", *, eligibility=ComparisonEligibilityStatus.COMPARABLE):
    return SimpleNamespace(
        trace=SimpleNamespace(trace_id="trace:comparison:local:reference:target"),
        before_experiment_id="reference",
        after_experiment_id="target",
        result_id="comparison:local:reference:target",
        eligibility=eligibility,
        ineligibility_reasons=(),
        acoustic_outcome=ExperimentAcousticOutcome(outcome),
        fact_deltas=(ExperimentFactDelta(
            fact_code="metric",
            before=2.0,
            after=1.0,
            delta=-1.0,
            unit="DB",
            change=ExperimentFactChange.IMPROVED,
            threshold=1.0,
            source_analysis_codes=("fixture",),
        ),),
        provenance_codes=("reference", "target"),
    )


def analysis(*, local=(), cumulative=()):
    return SimpleNamespace(sequence=SimpleNamespace(
        local_comparisons=local,
        cumulative_comparisons=cumulative,
    ))


def selected(service, source, qualifications):
    return service.qualify(
        analysis(local=(source,)), source.trace.trace_id, qualifications
    )


@pytest.mark.parametrize(
    ("outcome", "expected"),
    (
        ("IMPROVED", "BETTER"),
        ("DEGRADED", "WORSE"),
        ("UNCHANGED", "EQUIVALENT"),
        ("MIXED", "INDETERMINATE"),
        ("INCONCLUSIVE", "INDETERMINATE"),
    ),
)
def test_qualifies_only_an_exact_comparable_selection(outcome, expected):
    source = comparison(outcome)
    result = selected(
        PlacementComparisonSelectionQualificationService(),
        source,
        (
            qualification("reference", ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED),
            qualification("target", ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED),
        ),
    )

    assert result.comparison is source
    assert result.placement_qualification.comparison_status.value == expected
    assert result.placement_qualification.reference_experiment_id == "reference"
    assert result.placement_qualification.target_experiment_id == "target"
    assert result.blocking_reason_codes == ()
    assert result.causality_status == "NOT_ESTABLISHED"


@pytest.mark.parametrize("experiment_id", ("reference", "target"))
def test_missing_repeatability_qualification_blocks_without_projecting_a_verdict(
    experiment_id,
):
    source = comparison()
    known = "target" if experiment_id == "reference" else "reference"
    projector = SimpleNamespace(qualify=lambda value: pytest.fail("must not qualify"))
    result = selected(
        PlacementComparisonSelectionQualificationService(projector),
        source,
        (qualification(known, ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED),),
    )

    assert result.placement_qualification is None
    assert result.blocking_reason_codes == ("REPEATABILITY_QUALIFICATION_MISSING",)


@pytest.mark.parametrize(
    "status",
    (
        ChannelIsolationRepeatabilityQualificationStatus.NOT_QUALIFIED,
        ChannelIsolationRepeatabilityQualificationStatus.INDETERMINATE,
    ),
)
def test_existing_guard_block_prevents_placement_projection(status):
    source = comparison(eligibility=ComparisonEligibilityStatus.NOT_COMPARABLE)
    source.ineligibility_reasons = (SimpleNamespace(value="guard-blocked"),)
    projector = SimpleNamespace(qualify=lambda value: pytest.fail("must not qualify"))
    result = selected(
        PlacementComparisonSelectionQualificationService(projector),
        source,
        (
            qualification("reference", status),
            qualification("target", ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED),
        ),
    )

    assert result.placement_qualification is None
    assert result.blocking_reason_codes == ("guard-blocked",)


def test_duplicate_experiment_identity_is_rejected_deterministically():
    source = comparison()

    with pytest.raises(
        ValueError, match="REPEATABILITY_QUALIFICATION_AMBIGUOUS: reference"
    ):
        selected(
            PlacementComparisonSelectionQualificationService(),
            source,
            (
                qualification("reference", ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED),
                qualification("target", ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED),
                qualification("reference", ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED),
            ),
        )


def test_exact_resolution_is_independent_of_qualification_order():
    source = comparison()
    qualifications = (
        qualification("reference", ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED),
        qualification("target", ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED),
    )
    service = PlacementComparisonSelectionQualificationService()

    assert selected(service, source, qualifications) == selected(
        service, source, tuple(reversed(qualifications))
    )
