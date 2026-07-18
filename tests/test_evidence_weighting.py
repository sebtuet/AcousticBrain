from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.analysis import (
    DeterministicCorrectiveActionEngine,
    DeterministicEvidenceWeightingEngine,
)
from acousticbrain.models import (
    AcousticObservationSynthesis,
    CorrectiveActionApplicability,
    DeterministicAcousticReasoningSynthesis,
    DeterministicCorrectiveActionSynthesis,
    DeterministicEvidenceWeightingSynthesis,
    DeterministicReasoningConclusion,
    EvidenceDimension,
    EvidenceDimensionCeiling,
    EvidenceWeightLevel,
    WeightedActionApplicability,
)
from acousticbrain.report import (
    DeterministicEvidenceWeightingConsoleReporter,
    DeterministicEvidenceWeightingPresenter,
    Report,
)


def observation(observation_id="OBSERVATION_A", *, contradicting=()):
    return SimpleNamespace(
        observation_id=observation_id,
        confidence=80.0,
        supporting_evidence=(f"evidence.{observation_id}",),
        contradicting_evidence=tuple(contradicting),
        limitations=(),
    )


def reasoning(
    conclusion=DeterministicReasoningConclusion.SUPPORTED,
    *,
    reasoning_id="REASONING_A",
    observation_ids=("OBSERVATION_A",),
    contradictions=(),
):
    return SimpleNamespace(
        reasoning_id=reasoning_id,
        conclusion=conclusion,
        confidence=70.0,
        compatible_hypothesis_ids=("TARGET_A",),
        observation_ids=tuple(observation_ids),
        upstream_source_ids=("AnalysisA",),
        supporting_evidence=(f"reasoning.evidence.{reasoning_id}",),
        contradicting_evidence=tuple(contradictions),
        limitations=(),
    )


def action_for(source, *, plans=()):
    return DeterministicCorrectiveActionEngine().synthesize(
        SimpleNamespace(reasonings=(source,)),
        plans_by_target={"TARGET_A": tuple(plans)},
    ).actions[0]


def weigh(source=None, source_observation=None, *, plans=()):
    source = source or reasoning()
    source_observation = source_observation or observation()
    action = action_for(source, plans=plans)
    synthesis = DeterministicEvidenceWeightingEngine().weigh(
        SimpleNamespace(observations=(source_observation,)),
        SimpleNamespace(reasonings=(source,)),
        SimpleNamespace(actions=(action,)),
    )
    return source_observation, source, action, synthesis.weights[0]


def test_no_existing_evidence_produces_no_weight():
    result = DeterministicEvidenceWeightingEngine().weigh(
        AcousticObservationSynthesis(),
        DeterministicAcousticReasoningSynthesis(),
        DeterministicCorrectiveActionSynthesis(),
    )

    assert result == DeterministicEvidenceWeightingSynthesis()


def test_convergent_evidence_keeps_dimensions_independent():
    source = reasoning(observation_ids=("OBSERVATION_A", "OBSERVATION_B"))
    action = action_for(source, plans=("plan.ready",))
    weight = DeterministicEvidenceWeightingEngine().weigh(
        SimpleNamespace(observations=(observation(), observation("OBSERVATION_B"))),
        SimpleNamespace(reasonings=(source,)),
        SimpleNamespace(actions=(action,)),
    ).weights[0]

    assert weight.evidence_strength is EvidenceWeightLevel.HIGH
    assert weight.source_consistency is EvidenceWeightLevel.HIGH
    assert weight.discriminative_power is EvidenceWeightLevel.HIGH
    assert weight.parameter_completeness is EvidenceWeightLevel.HIGH
    assert weight.action_applicability is WeightedActionApplicability.APPLICABLE
    assert not hasattr(weight, "global_score")


def test_contradiction_caps_consistency_and_preserves_strength():
    source = reasoning(
        DeterministicReasoningConclusion.CONTRADICTORY_EVIDENCE,
        contradictions=("counter.evidence",),
    )
    source.observation_ids = ("OBSERVATION_A", "OBSERVATION_B")
    action = action_for(source)
    weight = DeterministicEvidenceWeightingEngine().weigh(
        SimpleNamespace(observations=(observation(), observation("OBSERVATION_B"))),
        SimpleNamespace(reasonings=(source,)),
        SimpleNamespace(actions=(action,)),
    ).weights[0]

    assert weight.evidence_strength is EvidenceWeightLevel.HIGH
    assert weight.source_consistency is EvidenceWeightLevel.LOW
    assert weight.action_applicability is WeightedActionApplicability.BLOCKED
    assert "counter.evidence" in weight.contradicting_evidence
    assert any(value.code == "CONTRADICTORY_EVIDENCE" for value in weight.blocking_factors)


def test_non_discriminated_reasoning_caps_only_discriminative_power():
    source = reasoning(DeterministicReasoningConclusion.NON_DISCRIMINATED)
    _, _, _, weight = weigh(source, plans=("plan.ready",))

    assert weight.discriminative_power is EvidenceWeightLevel.LOW
    assert weight.evidence_strength is EvidenceWeightLevel.LOW
    assert any(value.code == "INSUFFICIENT_DISCRIMINATION" for value in weight.blocking_factors)


def test_missing_parameters_remain_blocking_despite_strong_evidence():
    source = reasoning(observation_ids=("OBSERVATION_A", "OBSERVATION_B"))
    action = action_for(source)
    weight = DeterministicEvidenceWeightingEngine().weigh(
        SimpleNamespace(observations=(observation(), observation("OBSERVATION_B"))),
        SimpleNamespace(reasonings=(source,)),
        SimpleNamespace(actions=(action,)),
    ).weights[0]

    assert action.applicability is CorrectiveActionApplicability.BLOCKED_BY_MISSING_PARAMETERS
    assert weight.evidence_strength is EvidenceWeightLevel.HIGH
    assert weight.parameter_completeness is EvidenceWeightLevel.LOW
    assert weight.action_applicability is WeightedActionApplicability.BLOCKED
    assert any(value.code == "MISSING_PARAMETERS" for value in weight.blocking_factors)


def test_applicable_action_status_is_projected_not_recomputed():
    _, _, action, weight = weigh(plans=("plan.ready",))

    assert action.applicability is CorrectiveActionApplicability.APPLICABLE
    assert weight.action_applicability is WeightedActionApplicability.APPLICABLE


def test_explicit_ceilings_match_limited_dimensions():
    source = reasoning(
        DeterministicReasoningConclusion.CONTRADICTORY_EVIDENCE,
        contradictions=("counter.evidence",),
    )
    _, _, _, weight = weigh(source)

    assert {value.dimension for value in weight.ceilings} == {
        EvidenceDimension.SOURCE_CONSISTENCY,
        EvidenceDimension.DISCRIMINATIVE_POWER,
    }


def test_dimension_above_ceiling_is_rejected():
    _, _, _, weight = weigh(plans=("plan.ready",))
    ceiling = EvidenceDimensionCeiling(
        ceiling_id="ceiling.test",
        rule_id="rule.test",
        dimension=EvidenceDimension.EVIDENCE_STRENGTH,
        maximum=EvidenceWeightLevel.LOW,
        justification="test ceiling",
    )

    with pytest.raises(ValueError, match="exceeds"):
        replace(
            weight,
            evidence_strength=EvidenceWeightLevel.HIGH,
            ceilings=(ceiling,),
        )


def test_unknown_upstream_reference_is_rejected():
    source = reasoning(observation_ids=("UNKNOWN",))
    action = action_for(source, plans=("plan.ready",))

    with pytest.raises(ValueError, match="unknown upstream object"):
        DeterministicEvidenceWeightingEngine().weigh(
            SimpleNamespace(observations=(observation(),)),
            SimpleNamespace(reasonings=(source,)),
            SimpleNamespace(actions=(action,)),
        )


def test_weight_is_immutable_and_identifiers_are_stable():
    _, _, _, first = weigh(plans=("plan.ready",))
    _, _, _, second = weigh(plans=("plan.ready",))

    assert first == second
    assert first.weight_id == "EVIDENCE_WEIGHT_ACTION_RUN_CONTROLLED_MEASUREMENT_TARGET_A"
    with pytest.raises(FrozenInstanceError):
        first.evidence_strength = EvidenceWeightLevel.LOW


def test_weighting_does_not_mutate_any_upstream_object():
    source_observation = observation()
    source = reasoning()
    action = action_for(source, plans=("plan.ready",))
    before = tuple(dict(value.__dict__) for value in (source_observation, source, action))

    DeterministicEvidenceWeightingEngine().weigh(
        SimpleNamespace(observations=(source_observation,)),
        SimpleNamespace(reasonings=(source,)),
        SimpleNamespace(actions=(action,)),
    )

    assert tuple(dict(value.__dict__) for value in (source_observation, source, action)) == before


def test_report_is_byte_for_byte_reproducible(capsys):
    _, _, _, weight = weigh(plans=("plan.ready",))
    context = SimpleNamespace(
        deterministic_evidence_weighting_synthesis=(
            DeterministicEvidenceWeightingSynthesis((weight,))
        )
    )
    report = Report(project_name="weighting")
    report.deterministic_evidence_weighting = (
        DeterministicEvidenceWeightingPresenter().present(context)
    )
    reporter = DeterministicEvidenceWeightingConsoleReporter()

    reporter.print(report)
    first = capsys.readouterr().out
    reporter.print(report)
    second = capsys.readouterr().out

    assert first == second
    assert "GLOBAL SCORE" not in first


class RecordingBrain:
    def __init__(self):
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return Report(project_name="recorded")


class RecordingReporter:
    def print(self, report):
        pass


@pytest.mark.parametrize(
    ("extra", "expected"),
    (
        ([], {}),
        (["--observations"], {"synthesize_observations": True}),
        (["--reasoning"], {"synthesize_reasoning": True}),
        (["--actions"], {"synthesize_actions": True}),
        (["--weighting"], {"synthesize_weighting": True}),
    ),
)
def test_cli_modes_remain_strictly_separate(tmp_path, extra, expected):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    brain = RecordingBrain()

    acousticbrain_main.main(
        ["--measurements-root", str(campaign), *extra],
        brain=brain,
        reporter=RecordingReporter(),
    )

    assert brain.calls == [
        {
            "measurement_root": campaign,
            "compare_experiments": True,
            "analyze_causal_discrimination": True,
            **expected,
        }
    ]
