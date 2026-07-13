from dataclasses import replace
from types import SimpleNamespace

import pytest

from acousticbrain.application import (
    AcousticSession,
    AnalyzedExperiment,
    AutomaticExperimentComparisonService,
    ImportedExperiment,
    OptimizationSessionService,
)
from acousticbrain.models import (
    AcousticBrainState,
    ComparableExperimentFact,
    ComparisonEligibilityStatus,
    ComparisonIneligibilityReason,
    ExperimentComparisonType,
    ExperimentDescriptor,
    ExperimentEvolutionOutcome,
    ExperimentState,
    ExperimentType,
    ExperimentProtocol,
    OptimizationIteration,
    OptimizationSession,
    SessionHypothesis,
)


HYPOTHESIS = "ASYMMETRIC_SPEAKER_ROOM_INTERACTION"


def descriptor(
    experiment_id,
    *,
    baseline=False,
    parents=(),
    hypothesis=HYPOTHESIS,
    changes=(),
    required=(),
    content_hash=None,
):
    return ExperimentDescriptor(
        experiment_id=experiment_id,
        directory=f"/measurements/{experiment_id}",
        experiment_type=(
            ExperimentType.BASELINE if baseline else ExperimentType.EXPERIMENT
        ),
        available_files=(),
        available_channels=(),
        wav_files=(),
        txt_files=(),
        mdat_file=None,
        manifest_present=True,
        content_hash=content_hash or f"hash-{experiment_id}",
        timestamp=f"2026-07-{1 if baseline else int(experiment_id[4:7]) + 1:02d}",
        imported_at="2026-07-13T12:00:00+00:00",
        state=ExperimentState.READY,
        parent_experiment_ids=parents,
        source_protocol_id=(None if baseline or hypothesis is None else "protocol-1"),
        source_hypothesis_code=None if baseline else hypothesis,
        declared_change_codes=changes,
        required_comparison_fact_codes=required,
    )


def fact(
    value,
    *,
    code=None,
    unit="SCORE",
    family="ACOUSTIC_REASONING",
    readiness="AVAILABLE",
    threshold=2.0,
):
    code = code or f"hypothesis.{HYPOTHESIS}.support_score"
    return ComparableExperimentFact(
        code=code,
        value=value,
        unit=unit,
        family=family,
        semantic=code,
        source_analysis="AcousticReasoningAnalysis",
        threshold=threshold,
        higher_is_better=True,
        readiness=readiness,
    )


def state(experiment_id, support, status="SUPPORTED"):
    return AcousticBrainState(
        state_id=f"physical:{experiment_id}",
        measurement_name=experiment_id,
        global_score=50.0,
        facts=(),
        correlations=(),
        hypotheses=(SessionHypothesis(
            code=HYPOTHESIS,
            status=status,
            support_score=support,
            fact_codes=(),
            correlation_codes=(),
        ),),
    )


class Projector:
    def project(self, context):
        return context.facts


def comparison(
    monkeypatch, descriptors, supports, *, statuses=None, optimization_session=None
):
    statuses = statuses or {}
    monkeypatch.setattr(
        OptimizationSessionService,
        "snapshot_analysis",
        staticmethod(lambda context, *, state_id: context.state),
    )
    imported = tuple(ImportedExperiment(item, object()) for item in descriptors)
    session = AcousticSession("/measurements", imported)
    contexts = {
        item.experiment_id: SimpleNamespace(
            state=state(
                item.experiment_id,
                supports[item.experiment_id],
                statuses.get(item.experiment_id, "SUPPORTED"),
            ),
            facts=(fact(supports[item.experiment_id]),),
            confidence_analysis=SimpleNamespace(score=80.0),
        )
        for item in descriptors
    }
    return AutomaticExperimentComparisonService(Projector()).analyze(
        session,
        contexts,
        optimization_session=optimization_session,
        detailed_traceability=True,
    )


def test_builds_deterministic_local_and_cumulative_chronology(monkeypatch):
    descriptors = (
        descriptor("baseline", baseline=True),
        descriptor("exp-001"),
        descriptor("exp-002"),
    )
    result = comparison(
        monkeypatch, descriptors,
        {"baseline": 70.0, "exp-001": 75.0, "exp-002": 72.0},
    )

    assert result.sequence.chronology == ("baseline", "exp-001", "exp-002")
    assert [(item.before_experiment_id, item.after_experiment_id) for item in
            result.sequence.local_comparisons] == [
        ("baseline", "exp-001"), ("exp-001", "exp-002")
    ]
    assert [item.before_experiment_id for item in
            result.sequence.cumulative_comparisons] == ["baseline", "baseline"]


def test_explicit_parent_has_priority_and_ambiguous_parent_is_not_guessed(monkeypatch):
    descriptors = (
        descriptor("baseline", baseline=True),
        descriptor("exp-001"),
        descriptor("exp-002", parents=("baseline",)),
        descriptor("exp-003", parents=("baseline", "exp-002")),
    )
    result = comparison(monkeypatch, descriptors, {
        "baseline": 70.0, "exp-001": 71.0, "exp-002": 72.0, "exp-003": 73.0,
    })

    assert result.sequence.local_comparisons[1].before_experiment_id == "baseline"
    ambiguous = result.sequence.local_comparisons[2]
    assert ambiguous.eligibility is ComparisonEligibilityStatus.NOT_COMPARABLE
    assert ComparisonIneligibilityReason.AMBIGUOUS_PARENT in ambiguous.ineligibility_reasons
    assert ambiguous.before_experiment_id == "UNRESOLVED"


@pytest.mark.parametrize(
    "after,status,outcome",
    [
        (75.0, "SUPPORTED", ExperimentEvolutionOutcome.STRONGER),
        (65.0, "SUPPORTED", ExperimentEvolutionOutcome.WEAKER),
        (70.5, "SUPPORTED", ExperimentEvolutionOutcome.UNCHANGED),
        (60.0, "CONTRADICTED", ExperimentEvolutionOutcome.CONTRADICTED),
    ],
)
def test_projects_all_deterministic_hypothesis_outcomes(
    monkeypatch, after, status, outcome
):
    descriptors = (descriptor("baseline", baseline=True), descriptor("exp-001"))
    result = comparison(
        monkeypatch,
        descriptors,
        {"baseline": 70.0, "exp-001": after},
        statuses={"exp-001": status},
    )

    assert result.sequence.local_comparisons[0].outcome is outcome
    assert result.sequence.local_comparisons[0].outcome.value != "CONFIRMED"


def test_missing_protocol_never_infers_hypothesis_from_directory_name(monkeypatch):
    descriptors = (
        descriptor("baseline", baseline=True),
        descriptor("exp-001-verify-asymmetry", hypothesis=None),
    )
    result = comparison(
        monkeypatch, descriptors,
        {"baseline": 70.0, "exp-001-verify-asymmetry": 90.0},
    )

    evolution = result.sequence.local_comparisons[0]
    assert evolution.source_hypothesis_code is None
    assert evolution.outcome is ExperimentEvolutionOutcome.INCONCLUSIVE


def analyzed(item, facts):
    return AnalyzedExperiment(
        descriptor=item,
        context=object(),
        state=state(item.experiment_id, 70.0),
        facts=tuple(facts),
        technical_confidence=80.0,
    )


def test_fact_comparability_requires_same_unit_and_available_readiness():
    service = AutomaticExperimentComparisonService()
    before_descriptor = descriptor("baseline", baseline=True)
    after_descriptor = descriptor("exp-001")

    _, unit_reasons, _ = service._fact_deltas(
        analyzed(before_descriptor, (fact(10.0, unit="DB"),)),
        analyzed(after_descriptor, (fact(12.0, unit="SECONDS"),)),
    )
    _, readiness_reasons, unavailable = service._fact_deltas(
        analyzed(before_descriptor, (fact(10.0, readiness="BLOCKED"),)),
        analyzed(after_descriptor, (fact(12.0),)),
    )

    assert unit_reasons == (ComparisonIneligibilityReason.INCOMPATIBLE_UNIT,)
    assert readiness_reasons == (ComparisonIneligibilityReason.READINESS_BLOCKED,)
    assert unavailable == (f"hypothesis.{HYPOTHESIS}.support_score",)


def test_fact_comparability_rejects_family_and_semantic_mismatches():
    service = AutomaticExperimentComparisonService()
    before_descriptor = descriptor("baseline", baseline=True)
    after_descriptor = descriptor("exp-001")
    base = fact(10.0)

    _, family_reasons, _ = service._fact_deltas(
        analyzed(before_descriptor, (base,)),
        analyzed(after_descriptor, (replace(base, family="SPATIAL", value=12.0),)),
    )
    _, semantic_reasons, _ = service._fact_deltas(
        analyzed(before_descriptor, (base,)),
        analyzed(after_descriptor, (replace(base, semantic="another", value=12.0),)),
    )

    assert family_reasons == (ComparisonIneligibilityReason.INCOMPATIBLE_FAMILY,)
    assert semantic_reasons == (ComparisonIneligibilityReason.INCOMPATIBLE_SEMANTICS,)


def test_absent_fact_remains_unavailable_and_subthreshold_delta_is_unchanged():
    service = AutomaticExperimentComparisonService()
    before_descriptor = descriptor("baseline", baseline=True)
    after_descriptor = descriptor("exp-001")
    deltas, _, unavailable = service._fact_deltas(
        analyzed(before_descriptor, (
            fact(10.0), fact(None, code="missing"), fact(2.0, code="before-only"),
        )),
        analyzed(after_descriptor, (
            fact(11.0), fact(1.0, code="missing"), fact(2.0, code="after-only"),
        )),
    )

    assert deltas[0].change.value == "UNCHANGED"
    assert unavailable == ("after-only", "before-only", "missing")


def test_controlled_swap_reduces_but_does_not_erase_causal_limits(monkeypatch):
    descriptors = (
        descriptor("baseline", baseline=True),
        descriptor("exp-001", changes=("LEFT_RIGHT_REMEASUREMENT",)),
        descriptor("exp-002", changes=("CONTROLLED_LOUDSPEAKER_SWAP",)),
    )
    result = comparison(monkeypatch, descriptors, {
        "baseline": 70.0, "exp-001": 75.0, "exp-002": 80.0,
    })

    first = {item.code for item in result.sequence.local_comparisons[0].unresolved_discriminations}
    swapped = {item.code for item in result.sequence.local_comparisons[1].unresolved_discriminations}
    assert "LOUDSPEAKER_VS_ROOM_SIDE" in first
    assert "LOUDSPEAKER_VS_ROOM_SIDE" not in swapped
    assert "LOUDSPEAKER_VS_SIGNAL_CHAIN" in swapped


def test_repeated_pair_produces_reproducibility_facts_without_confirming_a_cause():
    service = AutomaticExperimentComparisonService()
    spatial = "spatial.left_right.level_difference_abs_db"
    deltas, _, _ = service._fact_deltas(
        analyzed(descriptor("baseline", baseline=True), (
            fact(3.0, code=spatial, unit="DB", family="SPATIAL", threshold=0.5),
        )),
        analyzed(descriptor("exp-001"), (
            fact(3.1, code=spatial, unit="DB", family="SPATIAL", threshold=0.5),
        )),
    )

    observed, _ = service._observations(
        HYPOTHESIS, deltas, ("LEFT_RIGHT_REMEASUREMENT",)
    )

    assert {item.code for item in observed} >= {
        "LEFT_RIGHT_DIFFERENCE_REPRODUCIBLE",
        "CHANNEL_SPECIFIC_PATTERN_STABLE",
    }


def test_expected_change_with_identical_hash_and_missing_required_fact_is_ineligible(
    monkeypatch,
):
    descriptors = (
        descriptor("baseline", baseline=True, content_hash="same"),
        descriptor(
            "exp-001",
            changes=("CONTROLLED_LOUDSPEAKER_SWAP",),
            required=("spatial.required",),
            content_hash="same",
        ),
    )
    result = comparison(
        monkeypatch, descriptors, {"baseline": 70.0, "exp-001": 75.0}
    ).sequence.local_comparisons[0]

    assert result.eligibility is ComparisonEligibilityStatus.NOT_COMPARABLE
    assert ComparisonIneligibilityReason.IDENTICAL_CONTENT in result.ineligibility_reasons
    assert ComparisonIneligibilityReason.REQUIRED_FACT_UNAVAILABLE in result.ineligibility_reasons


def test_physical_comparison_does_not_create_business_session_or_iteration(monkeypatch):
    descriptors = (descriptor("baseline", baseline=True), descriptor("exp-001"))
    result = comparison(
        monkeypatch, descriptors, {"baseline": 70.0, "exp-001": 75.0}
    )

    assert result.sequence.local_comparisons
    assert all(item.comparison_type is ExperimentComparisonType.LOCAL
               for item in result.sequence.local_comparisons)


def test_explicit_pr025_protocol_is_used_without_mutating_its_session(monkeypatch):
    descriptors = (
        descriptor("baseline", baseline=True),
        descriptor("exp-001", hypothesis=None),
    )
    protocol = ExperimentProtocol(
        experiment_id="exp-001",
        hypothesis_code=HYPOTHESIS,
        action_code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
        label="Repeated LEFT/RIGHT measurements",
        fact_codes=(),
    )
    session = OptimizationSession(
        session_id="explicit-session",
        iterations=[OptimizationIteration(
            number=1,
            protocol=protocol,
            before_state_id="explicit-state",
        )],
    )

    result = comparison(
        monkeypatch,
        descriptors,
        {"baseline": 70.0, "exp-001": 75.0},
        optimization_session=session,
    ).sequence.local_comparisons[0]

    assert result.source_protocol_id == "exp-001"
    assert result.source_hypothesis_code == HYPOTHESIS
    assert result.outcome is ExperimentEvolutionOutcome.STRONGER
    assert len(session.iterations) == 1
    assert session.iterations[0].comparison is None
