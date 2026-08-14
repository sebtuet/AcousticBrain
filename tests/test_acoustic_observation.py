from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.analysis import DeterministicAcousticObservationSynthesizer
from acousticbrain.models import (
    AcousticObservation,
    AcousticObservationCategory,
    AcousticObservationSynthesis,
)
from acousticbrain.report import (
    AcousticObservationConsoleReporter,
    AcousticObservationPresenter,
    Report,
)


def empty_context(**values):
    defaults = {
        "measurement_quality_analysis": None,
        "bass_decay_analysis": None,
        "rt60_analysis": None,
        "etc_analysis": None,
        "clarity_analysis": None,
        "stereo": None,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def rt60_analysis(confidence=82.5):
    return SimpleNamespace(
        broadband_rt60_seconds=0.47,
        minimum_rt60_seconds=0.41,
        maximum_rt60_seconds=0.53,
        left_right_band_differences_seconds={1000.0: -0.03},
        confidence=confidence,
    )


def etc_analysis():
    return SimpleNamespace(
        common_event_count=3,
        left_only_event_count=1,
        right_only_event_count=2,
        confidence=74.0,
    )


def synthesize(context):
    return DeterministicAcousticObservationSynthesizer().synthesize(context)


def test_no_analysis_produces_no_observation():
    assert synthesize(empty_context()).observations == ()


def test_one_established_analysis_produces_one_observation():
    result = synthesize(empty_context(rt60_analysis=rt60_analysis()))

    assert tuple(item.observation_id for item in result.observations) == (
        "DECAY_RT60_FACTS",
    )
    assert result.observations[0].confidence == 82.5


def test_multiple_analyses_produce_stably_ordered_observations():
    result = synthesize(
        empty_context(rt60_analysis=rt60_analysis(), etc_analysis=etc_analysis())
    )

    assert tuple(item.observation_id for item in result.observations) == (
        "DECAY_RT60_FACTS",
        "EARLY_REFLECTION_EVENT_FACTS",
    )


def test_existing_contradicting_analysis_facts_are_preserved_without_invention():
    issue = SimpleNamespace(code=SimpleNamespace(value="CHANNEL_TIMING_MISMATCH"))
    quality = SimpleNamespace(
        channel_qualities=(
            SimpleNamespace(
                channel=SimpleNamespace(value="LEFT"),
                issues=(issue,),
            ),
        ),
        measurement_set_quality=None,
        confidence=91.0,
    )

    observation = synthesize(
        empty_context(measurement_quality_analysis=quality)
    ).observations[0]

    assert observation.contradicting_evidence == (
        "measurement_quality.LEFT.CHANNEL_TIMING_MISMATCH",
    )
    assert observation.confidence == 91.0


def test_identical_analyses_produce_exactly_identical_results():
    context = empty_context(rt60_analysis=rt60_analysis(), etc_analysis=etc_analysis())
    engine = DeterministicAcousticObservationSynthesizer()

    assert engine.synthesize(context) == engine.synthesize(context)


def test_result_does_not_mutate_source_analyses():
    analysis = rt60_analysis()
    before = dict(analysis.__dict__)

    synthesize(empty_context(rt60_analysis=analysis))

    assert analysis.__dict__ == before


def test_observation_and_collections_are_immutable():
    observation = synthesize(empty_context(rt60_analysis=rt60_analysis())).observations[0]

    with pytest.raises(FrozenInstanceError):
        observation.title = "changed"
    with pytest.raises(TypeError):
        observation.supporting_evidence[0] = "changed"


def test_synthesis_rejects_duplicate_stable_ids():
    observation = synthesize(empty_context(rt60_analysis=rt60_analysis())).observations[0]

    with pytest.raises(ValueError, match="unique"):
        AcousticObservationSynthesis((observation, observation))


@pytest.mark.parametrize(
    "forbidden",
    (
        "déplacer les enceintes",
        "utiliser un panneau",
        "essayer un EQ",
        "faire une expérience",
        "je recommande",
    ),
)
def test_model_rejects_action_or_recommendation_language(forbidden):
    with pytest.raises(ValueError, match="descriptive"):
        AcousticObservation(
            observation_id="TEST",
            category=AcousticObservationCategory.GENERAL,
            title="Objective fact",
            description=forbidden,
            confidence=50.0,
            supporting_evidence=("fact=value",),
            contradicting_evidence=(),
            limitations=(),
            source_analysis_ids=("TestAnalysis",),
        )


def test_presenter_preserves_order_and_traceability():
    synthesis = synthesize(
        empty_context(rt60_analysis=rt60_analysis(), etc_analysis=etc_analysis())
    )

    presented = AcousticObservationPresenter().present(
        SimpleNamespace(acoustic_observation_synthesis=synthesis)
    )

    assert tuple(item.observation_id for item in presented.observations) == (
        "DECAY_RT60_FACTS",
        "EARLY_REFLECTION_EVENT_FACTS",
    )
    assert presented.observations[0].source_analysis_ids == ("RT60Analysis",)


def test_dedicated_report_is_descriptive_only(capsys):
    synthesis = synthesize(empty_context(rt60_analysis=rt60_analysis()))
    report = Report(project_name="objective-project")
    report.acoustic_observations = AcousticObservationPresenter().present(
        SimpleNamespace(acoustic_observation_synthesis=synthesis)
    )

    AcousticObservationConsoleReporter().print(report)
    output = capsys.readouterr().out.casefold()

    assert "deterministic acoustic observations" in output
    assert "decay_rt60_facts".casefold() in output
    assert "recommendation" not in output
    assert "action" not in output
    assert "hypothesis" not in output


class RecordingBrain:
    def __init__(self):
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return Report(project_name="recorded")


class RecordingReporter:
    def __init__(self):
        self.reports = []

    def print(self, report):
        self.reports.append(report)


def test_cli_observations_explicitly_enables_synthesis(tmp_path):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    brain = RecordingBrain()

    result = acousticbrain_main.main(
        ["--measurements-root", str(campaign), "--observations"],
        brain=brain,
        reporter=RecordingReporter(),
    )

    assert result == 0
    assert brain.calls == [
        {
            "measurement_root": campaign,
            "compare_experiments": True,
            "analyze_causal_discrimination": True,
            "synthesize_observations": True,
        }
    ]


def test_without_option_historical_call_is_strictly_unchanged(tmp_path):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    brain = RecordingBrain()

    acousticbrain_main.main(
        ["--measurements-root", str(campaign)],
        brain=brain,
        reporter=RecordingReporter(),
    )

    assert brain.calls == [
        {
            "measurement_root": campaign,
            "compare_experiments": True,
            "analyze_causal_discrimination": True,
            "synthesize_evidence_acquisition": True,
        }
    ]
