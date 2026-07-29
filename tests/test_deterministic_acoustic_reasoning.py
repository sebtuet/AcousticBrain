from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.analysis import DeterministicAcousticReasoningEngine
from acousticbrain.models import (
    AcousticObservation,
    AcousticObservationCategory,
    AcousticObservationSynthesis,
    CausalDiscriminationOutcome,
    DeterministicReasoningConclusion,
    HypothesisCode,
    HypothesisStatus,
    LongitudinalLearningStatus,
)
from acousticbrain.report import (
    DeterministicAcousticReasoningConsoleReporter,
    DeterministicAcousticReasoningPresenter,
    Report,
)


def observation(observation_id, *, confidence=80.0, contradictions=(), limits=()):
    return AcousticObservation(
        observation_id=observation_id,
        category=AcousticObservationCategory.GENERAL,
        title=f"Facts for {observation_id}",
        description=f"Structured facts are available for {observation_id}.",
        confidence=confidence,
        supporting_evidence=(f"{observation_id}.fact",),
        contradicting_evidence=contradictions,
        limitations=limits,
        source_analysis_ids=(f"{observation_id}.analysis",),
    )


def hypothesis(
    code=HypothesisCode.MODAL_BASS_PERSISTENCE,
    *,
    status=HypothesisStatus.SUPPORTED,
    confidence=75.0,
    supporting=("existing.support",),
    counter=(),
):
    return SimpleNamespace(
        code=code,
        status=status,
        confidence=confidence,
        supporting_evidence=tuple(SimpleNamespace(code=item) for item in supporting),
        counter_evidence=tuple(SimpleNamespace(code=item) for item in counter),
        missing_facts=(),
    )


def analysis(*hypotheses):
    return SimpleNamespace(hypotheses=tuple(hypotheses))


def synthesize(observations, *hypotheses, causal=None, longitudinal=None):
    return DeterministicAcousticReasoningEngine().synthesize(
        AcousticObservationSynthesis(tuple(observations)),
        acoustic_reasoning=analysis(*hypotheses),
        causal_discrimination=causal,
        longitudinal_learning=longitudinal,
    )


def modal_observations(**overrides):
    first = observation("LOW_FREQUENCY_DECAY_FACTS", **overrides)
    second = observation("DECAY_RT60_FACTS", **overrides)
    return first, second


def test_no_observation_produces_no_reasoning():
    assert synthesize((), hypothesis()).reasonings == ()


def test_one_observation_is_insufficient_for_a_conclusion():
    result = synthesize(
        (observation("LOW_FREQUENCY_DECAY_FACTS"),), hypothesis()
    )

    assert result.reasonings[0].conclusion is (
        DeterministicReasoningConclusion.INSUFFICIENT_EVIDENCE
    )


def test_converging_observations_explain_existing_supported_hypothesis():
    result = synthesize(modal_observations(), hypothesis())
    reasoning = result.reasonings[0]

    assert reasoning.conclusion is DeterministicReasoningConclusion.SUPPORTED
    assert reasoning.confidence == 75.0
    assert reasoning.compatible_hypothesis_ids == ("MODAL_BASS_PERSISTENCE",)


def test_observation_contradiction_prevents_strong_conclusion():
    values = (
        observation(
            "LOW_FREQUENCY_DECAY_FACTS",
            contradictions=("measurement.conflict",),
        ),
        observation("DECAY_RT60_FACTS"),
    )

    reasoning = synthesize(values, hypothesis()).reasonings[0]

    assert reasoning.conclusion is (
        DeterministicReasoningConclusion.CONTRADICTORY_EVIDENCE
    )
    assert "measurement.conflict" in reasoning.contradicting_evidence


def causal(outcome, counter=()):
    return SimpleNamespace(
        protocol_code="causal.protocol.v1",
        outcome=outcome,
        trajectory_assessments=(
            SimpleNamespace(counter_evidence_codes=tuple(counter)),
        ),
    )


def longitudinal(code, status):
    return SimpleNamespace(
        states=(
            SimpleNamespace(
                hypothesis_code=code.value,
                state_id=f"longitudinal:{code.value.lower()}",
                learning_status=status,
            ),
        )
    )


def asymmetry_observations():
    return (
        observation("STEREO_PEAK_DISTRIBUTION_FACTS"),
        observation("EARLY_REFLECTION_EVENT_FACTS"),
    )


def test_causal_result_can_corroborate_existing_hypothesis_status():
    value = synthesize(
        asymmetry_observations(),
        hypothesis(HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION),
        causal=causal(CausalDiscriminationOutcome.DISCRIMINATED),
    ).reasonings[0]

    assert value.conclusion is DeterministicReasoningConclusion.SUPPORTED
    assert any(premise.source_type.value == "CAUSAL_RESULT" for premise in value.premises)


def test_inconclusive_causal_result_keeps_conclusion_non_discriminated():
    value = synthesize(
        asymmetry_observations(),
        hypothesis(HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION),
        causal=causal(CausalDiscriminationOutcome.INCONCLUSIVE),
    ).reasonings[0]

    assert value.conclusion is DeterministicReasoningConclusion.NON_DISCRIMINATED


def test_contradictory_causal_result_is_visible_and_blocks_conclusion():
    value = synthesize(
        asymmetry_observations(),
        hypothesis(HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION),
        causal=causal(CausalDiscriminationOutcome.CONTRADICTORY, ("causal.counter",)),
    ).reasonings[0]

    assert value.conclusion is DeterministicReasoningConclusion.CONTRADICTORY_EVIDENCE
    assert "causal_discrimination.outcome.CONTRADICTORY" in (
        value.contradicting_evidence
    )


def test_longitudinal_stable_non_support_blocks_strong_conclusion():
    value = synthesize(
        modal_observations(),
        hypothesis(),
        longitudinal=longitudinal(
            HypothesisCode.MODAL_BASS_PERSISTENCE,
            LongitudinalLearningStatus.STABLE_NON_SUPPORT,
        ),
    ).reasonings[0]

    assert value.conclusion is DeterministicReasoningConclusion.CONTRADICTORY_EVIDENCE
    assert any(
        premise.role.value == "CONTRADICTING"
        and premise.source_type.value == "LONGITUDINAL_STATE"
        for premise in value.premises
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    (
        (HypothesisStatus.PLAUSIBLE, DeterministicReasoningConclusion.PARTIALLY_SUPPORTED),
        (HypothesisStatus.CONTRADICTED, DeterministicReasoningConclusion.CONTRADICTED),
        (HypothesisStatus.INCONCLUSIVE, DeterministicReasoningConclusion.NON_DISCRIMINATED),
    ),
)
def test_existing_hypothesis_status_is_explained_without_new_hypothesis(status, expected):
    value = synthesize(modal_observations(), hypothesis(status=status)).reasonings[0]

    assert value.conclusion is expected
    assert value.compatible_hypothesis_ids == (HypothesisCode.MODAL_BASS_PERSISTENCE.value,)


def test_reasoning_order_and_ids_are_stable():
    values = (
        *modal_observations(),
        *asymmetry_observations(),
        observation("CLARITY_C80_FACTS"),
    )
    hypotheses = (
        hypothesis(HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION),
        hypothesis(HypothesisCode.MODAL_BASS_PERSISTENCE),
        hypothesis(HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION),
    )

    result = synthesize(values, *hypotheses)

    assert tuple(item.reasoning_id for item in result.reasonings) == (
        "ASYMMETRIC_SPEAKER_ROOM_INTERACTION_REASONING",
        "MODAL_BASS_PERSISTENCE_REASONING",
        "DOMINANT_EARLY_REFLECTION_INTERACTION_REASONING",
    )


def test_each_inference_references_existing_premises_and_sources():
    reasoning = synthesize(modal_observations(), hypothesis()).reasonings[0]
    premise_ids = {item.premise_id for item in reasoning.premises}

    assert set(reasoning.inference_steps[0].input_premise_ids) == premise_ids
    assert set(reasoning.observation_ids) == {
        premise.source_id
        for premise in reasoning.premises
        if premise.source_type.value == "OBSERVATION"
    }


def test_models_and_collections_are_immutable():
    reasoning = synthesize(modal_observations(), hypothesis()).reasonings[0]

    with pytest.raises(FrozenInstanceError):
        reasoning.title = "changed"
    with pytest.raises(TypeError):
        reasoning.premises[0] = reasoning.premises[0]


def test_identical_inputs_and_report_are_byte_for_byte_reproducible(capsys):
    synthesis = synthesize(modal_observations(), hypothesis())
    context = SimpleNamespace(deterministic_acoustic_reasoning_synthesis=synthesis)
    report = Report(project_name="deterministic")
    report.deterministic_acoustic_reasoning = (
        DeterministicAcousticReasoningPresenter().present(context)
    )
    reporter = DeterministicAcousticReasoningConsoleReporter()

    reporter.print(report)
    first = capsys.readouterr().out
    reporter.print(report)
    second = capsys.readouterr().out

    assert first == second


def test_report_contains_no_action_or_recommendation_language(capsys):
    synthesis = synthesize(modal_observations(), hypothesis())
    report = Report(project_name="deterministic")
    report.deterministic_acoustic_reasoning = (
        DeterministicAcousticReasoningPresenter().present(
            SimpleNamespace(deterministic_acoustic_reasoning_synthesis=synthesis)
        )
    )

    DeterministicAcousticReasoningConsoleReporter().print(report)
    output = capsys.readouterr().out.casefold()

    for forbidden in ("vous devriez", "essayez", "déplacez", "installez", "priorisez"):
        assert forbidden not in output


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
        ([], {"synthesize_evidence_acquisition": True}),
        (["--observations"], {"synthesize_observations": True}),
        (["--reasoning"], {"synthesize_reasoning": True}),
    ),
)
def test_cli_modes_preserve_historical_and_observation_contracts(tmp_path, extra, expected):
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


def test_reasoning_does_not_create_hypotheses_or_actions():
    source_hypothesis = hypothesis()
    result = synthesize(modal_observations(), source_hypothesis)

    assert result.reasonings[0].compatible_hypothesis_ids == (
        source_hypothesis.code.value,
    )
    assert not hasattr(result.reasonings[0], "actions")
    assert not hasattr(result, "hypotheses")
