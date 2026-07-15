import copy
import inspect
from io import StringIO
from types import SimpleNamespace
from contextlib import redirect_stdout

from acousticbrain.analysis import LongitudinalExperimentalLearningEngine
from acousticbrain.brain.pipeline import BrainPipeline
from acousticbrain.models import (
    ComparisonEligibilityStatus,
    ExperimentEvolutionOutcome,
    ExperimentFactChange,
    ExperimentFactDelta,
    ExperimentInformationStatus,
    ExperimentKind,
    ExperimentCounterFact,
    LongitudinalLearningStatus,
    ObservedExperimentFact,
)
from acousticbrain.models.experiment_declaration import ExperimentDeclaration
from acousticbrain.report import (
    ConsoleReporter,
    LongitudinalExperimentalLearningPresenter,
    Report,
)


HYPOTHESIS = "TEST_HYPOTHESIS"
PROTOCOL = "protocol.test.v1"


def declaration(kind, reference="baseline"):
    if kind is ExperimentKind.UNKNOWN:
        return ExperimentDeclaration.unknown()
    modified = (
        ("MEASUREMENT_ACQUISITION",)
        if kind is ExperimentKind.MEASUREMENT_REPEAT
        else ("LOUDSPEAKER_POSITION",)
    )
    return ExperimentDeclaration(
        schema_version=1,
        experiment_kind=kind,
        reference_experiment_code=reference,
        modified_variables=modified,
        controlled_variables=("MICROPHONE_POSITION",),
        user_note=None,
        field_provenance=tuple(
            (field, "USER_DECLARATION")
            for field in (
                "experiment_kind",
                "reference_experiment_code",
                "modified_variables",
                "controlled_variables",
                "user_note",
            )
        ),
    )


def descriptor(code, kind=ExperimentKind.CONTROLLED_INTERVENTION,
               hypothesis=HYPOTHESIS, protocol=PROTOCOL, reference="baseline"):
    return SimpleNamespace(
        experiment_id=code,
        source_hypothesis_code=hypothesis,
        source_protocol_id=protocol,
        experiment_declaration=declaration(kind, reference),
    )


def comparison(
    code,
    *,
    hypothesis=HYPOTHESIS,
    protocol=PROTOCOL,
    kind=ExperimentKind.CONTROLLED_INTERVENTION,
    eligibility=ComparisonEligibilityStatus.COMPARABLE,
    outcome=ExperimentEvolutionOutcome.STRONGER,
    observed=("OBSERVED_SUPPORT",),
    counters=(),
    unchanged=(),
):
    deltas = tuple(
        ExperimentFactDelta(
            fact_code=value,
            before=1.0,
            after=1.0,
            delta=0.0,
            unit="SCORE",
            change=ExperimentFactChange.UNCHANGED,
            threshold=0.0,
            source_analysis_codes=("SyntheticAnalysis",),
        )
        for value in unchanged
    )
    return SimpleNamespace(
        result_id=f"comparison.local.{code}",
        after_experiment_id=code,
        source_hypothesis_code=hypothesis,
        source_protocol_id=protocol,
        experiment_kind=kind,
        eligibility=eligibility,
        outcome=outcome,
        observed_facts=tuple(
            ObservedExperimentFact(value, (value,), ("SyntheticAnalysis",))
            for value in observed
        ),
        counter_facts=tuple(
            ExperimentCounterFact(value, (value,), ("SyntheticAnalysis",))
            for value in counters
        ),
        fact_deltas=deltas,
    )


def analysis(*comparisons):
    return SimpleNamespace(sequence=SimpleNamespace(local_comparisons=comparisons))


def reasoning(*hypotheses):
    return SimpleNamespace(hypotheses=tuple(
        SimpleNamespace(code=SimpleNamespace(value=value)) for value in hypotheses
    ))


def run(*comparisons, descriptors=(), campaigns=(), causal=None,
        hypotheses=(HYPOTHESIS,)):
    return LongitudinalExperimentalLearningEngine().analyze(
        descriptors=descriptors,
        comparison_analysis=analysis(*comparisons),
        campaign_analyses=campaigns,
        causal_discrimination=causal,
        acoustic_reasoning=reasoning(*hypotheses),
    )


def state(result, hypothesis=HYPOTHESIS):
    return next(item for item in result.states if item.hypothesis_code == hypothesis)


def campaign(*, unresolved=(), next_code=None, status="RESOLVED",
             experiments=("exp-campaign",)):
    return SimpleNamespace(
        campaign_code="TEST_CAMPAIGN",
        protocol_id=PROTOCOL,
        hypothesis_code=HYPOTHESIS,
        measurements=tuple(
            SimpleNamespace(experiment_id=code) for code in experiments
        ),
        unresolved_discrimination_codes=unresolved,
        next_discrimination_code=next_code,
        status=SimpleNamespace(value=status),
        trace=SimpleNamespace(experiment_ids=experiments),
    )


def causal(*, remaining=(), resolved=(), deferred=(), recommended=None,
           experiments=("exp-causal",)):
    decisions = tuple(
        SimpleNamespace(
            discrimination_code=value,
            status=SimpleNamespace(value="DEFERRED"),
        )
        for value in deferred
    )
    return SimpleNamespace(
        protocol_code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
        completed_steps=tuple(
            SimpleNamespace(experiment_id=code) for code in experiments
        ),
        resolved_discrimination_codes=resolved,
        remaining_discrimination_codes=remaining,
        discrimination_decisions=decisions,
        recommended_next_protocol=recommended,
        trace=SimpleNamespace(
            trace_id="causal-trace:test",
            experiment_ids=experiments,
        ),
    )


def test_no_experiment_and_never_tested_hypothesis():
    value = state(run())
    assert value.learning_status is LongitudinalLearningStatus.NOT_TESTED
    assert value.historical_context_experiment_codes == ()


def test_comparable_controlled_intervention_accumulates_only_explicit_observations():
    item = comparison("exp-001")
    value = state(run(item, descriptors=(descriptor("exp-001"),)))
    assert value.learning_status is LongitudinalLearningStatus.EVIDENCE_ACCUMULATING
    assert value.controlled_intervention_codes == ("exp-001",)
    assert value.supporting_observation_ids == (
        "comparison.local.exp-001:OBSERVED_SUPPORT",
    )
    assert value.causality_status == "NOT_ESTABLISHED"


def test_non_comparable_and_unknown_declarations_are_excluded():
    blocked = comparison(
        "exp-bad", eligibility=ComparisonEligibilityStatus.NOT_COMPARABLE
    )
    unknown = comparison("exp-unknown", kind=ExperimentKind.UNKNOWN)
    result = run(
        blocked,
        unknown,
        descriptors=(
            descriptor("exp-bad"),
            descriptor("exp-unknown", ExperimentKind.UNKNOWN),
        ),
    )
    value = state(result)
    assert value.non_comparable_experiment_codes == ("exp-bad",)
    assert value.unknown_declaration_codes == ("exp-unknown",)
    assert value.supporting_observation_ids == ()
    assert value.learning_status is LongitudinalLearningStatus.INSUFFICIENT_DECLARATION


def test_measurement_repeat_informs_stability_without_supporting_positioning():
    repeat = comparison(
        "repeat-1",
        kind=ExperimentKind.MEASUREMENT_REPEAT,
        outcome=ExperimentEvolutionOutcome.UNCHANGED,
        observed=(),
        unchanged=("STABLE_FACT",),
    )
    value = state(run(
        repeat,
        descriptors=(descriptor("repeat-1", ExperimentKind.MEASUREMENT_REPEAT),),
    ))
    assert value.measurement_repeat_codes == ("repeat-1",)
    assert value.supporting_observation_ids == ()
    assert value.unchanged_observation_ids == (
        "comparison.local.repeat-1:STABLE_FACT",
    )
    assert value.next_information_need == "ADDITIONAL_REPEAT_FOR_STABILITY"


def test_repeat_with_mixed_result_never_invents_satisfactory_repeatability():
    repeat = comparison(
        "repeat-mixed",
        kind=ExperimentKind.MEASUREMENT_REPEAT,
        outcome=ExperimentEvolutionOutcome.INCONCLUSIVE,
    )
    value = state(run(
        repeat,
        descriptors=(descriptor("repeat-mixed", ExperimentKind.MEASUREMENT_REPEAT),),
    ))
    assert value.unchanged_observation_ids == ()
    assert value.inconclusive_observation_ids == (
        "comparison.local.repeat-mixed:REPEATABILITY_NOT_ESTABLISHED",
    )


def test_multiple_supports_conflicts_and_stable_non_support_are_rule_based():
    supports = (
        comparison("support-1", observed=("SAME_SUPPORT",)),
        comparison("support-2", observed=("SAME_SUPPORT",)),
    )
    result = run(*supports, descriptors=(descriptor("support-1"), descriptor("support-2")))
    assert state(result).learning_status is LongitudinalLearningStatus.STABLE_SUPPORT

    conflict = comparison("counter", counters=("COUNTER",), observed=())
    result = run(*supports, conflict, descriptors=(
        descriptor("support-1"), descriptor("support-2"), descriptor("counter")
    ))
    assert state(result).learning_status is LongitudinalLearningStatus.CONFLICTING_EVIDENCE

    counters = (
        comparison("counter-1", counters=("COUNTER_1",), observed=()),
        comparison("counter-2", counters=("COUNTER_2",), observed=()),
    )
    result = run(*counters, descriptors=(descriptor("counter-1"), descriptor("counter-2")))
    assert state(result).learning_status is LongitudinalLearningStatus.STABLE_NON_SUPPORT
    assert dict(state(result).evidence_summary)["CONTRADICTING"] == 2


def test_inconclusive_controlled_result_is_preserved():
    item = comparison(
        "exp-inc",
        outcome=ExperimentEvolutionOutcome.INCONCLUSIVE,
        observed=(),
    )
    value = state(run(item, descriptors=(descriptor("exp-inc"),)))
    assert value.inconclusive_observation_ids == (
        "comparison.local.exp-inc:INCONCLUSIVE",
    )


def test_unchanged_controlled_observations_are_preserved_without_support():
    item = comparison(
        "exp-stable",
        outcome=ExperimentEvolutionOutcome.UNCHANGED,
        observed=(),
        unchanged=("UNCHANGED_FACT",),
    )
    value = state(run(item, descriptors=(descriptor("exp-stable"),)))
    assert value.unchanged_observation_ids == (
        "comparison.local.exp-stable:UNCHANGED_FACT",
    )
    assert value.supporting_observation_ids == ()


def test_resolved_remaining_deferred_completed_and_exhausted_discriminations():
    value = state(run(
        campaigns=(campaign(unresolved=("MODAL_OPEN",), next_code="NEXT_MODAL"),),
        causal=causal(
            remaining=("ROOM_OPEN",),
            resolved=("CHAIN_RESOLVED",),
            deferred=("ROOM_OPEN",),
        ),
        hypotheses=(HYPOTHESIS, "ASYMMETRIC_SPEAKER_ROOM_INTERACTION"),
    ), "ASYMMETRIC_SPEAKER_ROOM_INTERACTION")
    assert value.resolved_ambiguities == ("CHAIN_RESOLVED",)
    assert value.completed_discriminations == ("CHAIN_RESOLVED",)
    assert value.remaining_ambiguities == ("ROOM_OPEN",)
    assert value.deferred_discriminations == ("ROOM_OPEN",)
    assert value.learning_status is LongitudinalLearningStatus.DEFERRED_BY_USER

    exhausted = state(run(
        campaigns=(campaign(),),
        descriptors=(descriptor("exp-campaign"),),
    ))
    assert exhausted.exhausted_discriminations == ("TEST_CAMPAIGN",)
    assert exhausted.learning_status is LongitudinalLearningStatus.EXPERIMENTAL_PATH_EXHAUSTED


def test_unknown_discrimination_sources_remain_historical_not_evidence():
    source = causal(
        remaining=("ROOM_OPEN",),
        resolved=("CHAIN_RESOLVED",),
        experiments=("exp-001", "exp-002"),
    )
    descriptors = (
        descriptor("exp-001", ExperimentKind.UNKNOWN),
        descriptor("exp-002", ExperimentKind.UNKNOWN),
    )
    value = state(run(
        descriptors=descriptors,
        causal=source,
        hypotheses=("ASYMMETRIC_SPEAKER_ROOM_INTERACTION",),
    ), "ASYMMETRIC_SPEAKER_ROOM_INTERACTION")

    assert value.evidence_contributing_experiment_codes == ()
    assert value.discrimination_source_experiment_codes == (
        "exp-001",
        "exp-002",
    )
    assert value.unknown_declaration_codes == ("exp-001", "exp-002")
    assert value.controlled_intervention_codes == ()
    assert value.supporting_observation_ids == ()
    provenance = value.resolved_ambiguity_provenance[0]
    assert provenance.ambiguity_code == "CHAIN_RESOLVED"
    assert provenance.protocol_code == "VERIFY_SPEAKER_ROOM_ASYMMETRY"
    assert provenance.source_id == "causal-trace:test"
    assert provenance.source_experiment_codes == ("exp-001", "exp-002")


def test_resolved_ambiguity_preserves_trace_when_experiments_are_unavailable():
    value = state(run(
        causal=causal(resolved=("CHAIN_RESOLVED",), experiments=()),
        hypotheses=("ASYMMETRIC_SPEAKER_ROOM_INTERACTION",),
    ), "ASYMMETRIC_SPEAKER_ROOM_INTERACTION")

    provenance = value.resolved_ambiguity_provenance[0]
    assert provenance.source_id == "causal-trace:test"
    assert provenance.source_experiment_codes == ()
    assert value.learning_status is LongitudinalLearningStatus.INSUFFICIENT_DECLARATION
    assert value.next_information_need == "DECLARE_HISTORICAL_EXPERIMENT_PROVENANCE"


def test_unknown_campaign_sources_are_historical_and_block_exhaustion():
    value = state(run(
        campaigns=(campaign(),),
        descriptors=(descriptor("exp-campaign", ExperimentKind.UNKNOWN),),
    ))

    assert value.campaign_source_experiment_codes == ("exp-campaign",)
    assert value.evidence_contributing_experiment_codes == ()
    assert value.unknown_declaration_codes == ("exp-campaign",)
    assert value.exhausted_discriminations == ("TEST_CAMPAIGN",)
    assert value.learning_status is LongitudinalLearningStatus.INSUFFICIENT_DECLARATION
    assert (
        value.next_information_need
        == "DECLARE_TESTED_VARIABLE_OR_UNCHANGED_CONFIGURATION"
    )


def test_different_hypotheses_are_never_aggregated_and_order_is_deterministic():
    first = comparison("one", hypothesis="HYP_B", observed=("B",))
    second = comparison("two", hypothesis="HYP_A", observed=("A",))
    result = run(
        first,
        second,
        descriptors=(
            descriptor("one", hypothesis="HYP_B"),
            descriptor("two", hypothesis="HYP_A"),
        ),
        hypotheses=("HYP_B", "HYP_A"),
    )
    assert tuple(item.hypothesis_code for item in result.states) == ("HYP_A", "HYP_B")
    assert state(result, "HYP_A").supporting_observation_ids == (
        "comparison.local.two:A",
    )
    assert result == run(
        first,
        second,
        descriptors=(
            descriptor("one", hypothesis="HYP_B"),
            descriptor("two", hypothesis="HYP_A"),
        ),
        hypotheses=("HYP_B", "HYP_A"),
    )
    assert state(result, "HYP_A").state_id == "longitudinal-learning:hyp_a"
    assert dict(state(result, "HYP_A").provenance)["comparisons"] == (
        "comparison.local.two",
    )


def test_information_assessment_exact_partial_new_and_still_informative():
    engine = LongitudinalExperimentalLearningEngine()
    existing = descriptor("existing")
    base = dict(
        hypothesis_code=HYPOTHESIS,
        protocol_code=PROTOCOL,
        experiment_kind=ExperimentKind.CONTROLLED_INTERVENTION,
        reference_experiment_code="baseline",
        modified_variables=("LOUDSPEAKER_POSITION",),
        controlled_variables=("MICROPHONE_POSITION",),
    )
    assert engine.assess_proposal((existing,), **base).status is ExperimentInformationStatus.EXACT_REPEAT
    partial = {**base, "controlled_variables": ("ROOM_CONFIGURATION",)}
    assert engine.assess_proposal((existing,), **partial).status is ExperimentInformationStatus.PARTIAL_REPEAT
    different = {**base, "protocol_code": "protocol.other.v1"}
    assert engine.assess_proposal((existing,), **different).status is ExperimentInformationStatus.STILL_INFORMATIVE
    new = {**base, "hypothesis_code": "NEW_HYPOTHESIS"}
    assert engine.assess_proposal((existing,), **new).status is ExperimentInformationStatus.NEW_INFORMATION


def test_information_assessment_blocking_and_completed_statuses():
    engine = LongitudinalExperimentalLearningEngine()
    base = dict(
        hypothesis_code=HYPOTHESIS,
        protocol_code=PROTOCOL,
        experiment_kind=ExperimentKind.CONTROLLED_INTERVENTION,
        reference_experiment_code="baseline",
        modified_variables=("LOUDSPEAKER_POSITION",),
        controlled_variables=("MICROPHONE_POSITION",),
    )
    assert engine.assess_proposal((), **{**base, "experiment_kind": ExperimentKind.UNKNOWN}).status is ExperimentInformationStatus.BLOCKED_BY_MISSING_DECLARATION
    assert engine.assess_proposal((), **base, comparable=False).status is ExperimentInformationStatus.BLOCKED_BY_NON_COMPARABILITY
    assert engine.assess_proposal((), **base, deferred=True).status is ExperimentInformationStatus.DEFERRED_BY_USER
    assert engine.assess_proposal((), **base, already_completed=True).status is ExperimentInformationStatus.ALREADY_COMPLETED


def test_engine_does_not_mutate_sources_or_external_decisions():
    item = comparison("immutable")
    sources = analysis(item)
    recommendation = SimpleNamespace(score=42.0)
    ranking = SimpleNamespace(order=("a", "b"))
    positioning = SimpleNamespace(eligible=True)
    before = copy.deepcopy((sources, recommendation, ranking, positioning))
    run(item, descriptors=(descriptor("immutable"),))
    assert (sources, recommendation, ranking, positioning) == before


def test_technical_report_is_deterministic_non_causal_and_not_duplicated():
    item = comparison("report")
    result = run(item, descriptors=(descriptor("report"),))
    context = SimpleNamespace(longitudinal_experimental_learning_analysis=result)
    report = Report(project_name="synthetic")
    report.longitudinal_experimental_learning = (
        LongitudinalExperimentalLearningPresenter().present(context)
    )

    def render():
        stream = StringIO()
        with redirect_stdout(stream):
            ConsoleReporter().print(report)
        return stream.getvalue()

    output = render()
    assert output == render()
    assert output.count("APPRENTISSAGE EXPÉRIMENTAL") == 1
    assert "Causalité : NOT_ESTABLISHED" in output
    forbidden = (
        "causalité confirmée",
        "hypothèse définitivement prouvée",
        "apprentissage automatique",
        "modèle entraîné",
        "position optimale",
    )
    assert all(value not in output.lower() for value in forbidden)


def test_report_separates_historical_discrimination_from_evidence_contributors():
    result = run(
        descriptors=(
            descriptor("exp-001", ExperimentKind.UNKNOWN),
            descriptor("exp-002", ExperimentKind.UNKNOWN),
        ),
        causal=causal(
            remaining=("ROOM_OPEN",),
            resolved=("CHAIN_RESOLVED",),
            experiments=("exp-001", "exp-002"),
        ),
        hypotheses=("ASYMMETRIC_SPEAKER_ROOM_INTERACTION",),
    )
    context = SimpleNamespace(longitudinal_experimental_learning_analysis=result)
    report = Report(project_name="historical-discrimination")
    report.longitudinal_experimental_learning = (
        LongitudinalExperimentalLearningPresenter().present(context)
    )
    stream = StringIO()
    with redirect_stdout(stream):
        ConsoleReporter().print(report)
    output = stream.getvalue()

    assert "Preuves longitudinales admissibles : aucune" in output
    assert "Historique expérimental conservé — discrimination :" in output
    assert "exp-001 — déclaration expérimentale historique non disponible" in output
    assert "Historique non admissible comme nouvelle preuve :" in output
    assert "CHAIN_RESOLVED" in output
    assert "VERIFY_SPEAKER_ROOM_ASYMMETRY — causal-trace:test" in output
    assert "Historique expérimental de la trace : exp-001, exp-002" in output
    assert "ne sont pas requalifiées comme interventions contrôlées" in output
    assert "Expériences utilisées : aucune" not in output
    assert "Expériences utilisées par la discrimination historique" not in output


def test_precomputed_learning_state_is_exposed_before_experiment_planning():
    source = inspect.getsource(BrainPipeline.run)

    assert source.index(
        "context.longitudinal_experimental_learning_analysis ="
    ) < source.index("ExperimentPlanningStage().run")


def test_exp006_analogue_unknown_mixed_does_not_support_positioning():
    item = comparison(
        "exp-006",
        kind=ExperimentKind.UNKNOWN,
        outcome=ExperimentEvolutionOutcome.INCONCLUSIVE,
        observed=("PLACEMENT_SCORE_CHANGED",),
    )
    value = state(run(
        item,
        descriptors=(descriptor("exp-006", ExperimentKind.UNKNOWN),),
    ))
    assert value.learning_status is LongitudinalLearningStatus.INSUFFICIENT_DECLARATION
    assert value.supporting_observation_ids == ()
    assert value.contradicting_observation_ids == ()
    assert value.causality_status == "NOT_ESTABLISHED"
