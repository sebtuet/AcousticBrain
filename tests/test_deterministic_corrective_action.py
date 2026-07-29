from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.analysis import DeterministicCorrectiveActionEngine
from acousticbrain.brain.stages.deterministic_corrective_action import (
    DeterministicCorrectiveActionStage,
)
from acousticbrain.models import (
    CorrectiveActionApplicability,
    CorrectiveActionPriority,
    CorrectiveActionType,
    DeterministicCorrectiveActionSynthesis,
    DeterministicReasoningConclusion,
    ListeningPositionCampaignPlanStatus,
)
from acousticbrain.report import (
    DeterministicCorrectiveActionConsoleReporter,
    DeterministicCorrectiveActionPresenter,
    Report,
)


def reasoning(
    conclusion=DeterministicReasoningConclusion.SUPPORTED,
    *,
    reasoning_id="DOMINANT_EARLY_REFLECTION_INTERACTION_REASONING",
    target="DOMINANT_EARLY_REFLECTION_INTERACTION",
    confidence=70.0,
    contradictions=(),
):
    return SimpleNamespace(
        reasoning_id=reasoning_id,
        conclusion=conclusion,
        confidence=confidence,
        compatible_hypothesis_ids=(target,),
        observation_ids=("EARLY_REFLECTION_EVENT_FACTS", "CLARITY_C80_FACTS"),
        upstream_source_ids=("ETCAnalysis", "ClarityAnalysis"),
        contradicting_evidence=tuple(contradictions),
        limitations=(),
    )


def synthesize(
    *reasonings,
    protocols=None,
    plans=None,
    tested=(),
    invalidated=(),
):
    return DeterministicCorrectiveActionEngine().synthesize(
        SimpleNamespace(reasonings=tuple(reasonings)),
        protocols_by_target=protocols,
        plans_by_target=plans,
        tested_action_ids=tested,
        invalidated_action_ids=invalidated,
    )


def supported_with_plan(**values):
    source = reasoning(**values)
    result = synthesize(
        source,
        plans={source.compatible_hypothesis_ids[0]: ("reflection-plan-001",)},
    )
    return source, result.actions[0]


def test_no_reasoning_produces_no_action():
    assert synthesize().actions == ()


def test_supported_reasoning_with_existing_plan_produces_applicable_action():
    _, action = supported_with_plan()

    assert action.applicability is CorrectiveActionApplicability.APPLICABLE
    assert action.action_type is CorrectiveActionType.RUN_CONTROLLED_MEASUREMENT
    assert action.compatible_plan_ids == ("reflection-plan-001",)


def test_supported_reasoning_without_required_contract_is_blocked():
    action = synthesize(reasoning()).actions[0]

    assert action.applicability is (
        CorrectiveActionApplicability.BLOCKED_BY_MISSING_PARAMETERS
    )
    assert action.required_missing_parameters == (
        "compatible_protocol_or_plan_id",
    )


def test_non_discriminated_reasoning_only_produces_discrimination_measurement():
    source = reasoning(
        DeterministicReasoningConclusion.NON_DISCRIMINATED,
        target="MODAL_BASS_PERSISTENCE",
        reasoning_id="MODAL_BASS_PERSISTENCE_REASONING",
    )
    action = synthesize(
        source,
        protocols={"MODAL_BASS_PERSISTENCE": ("sampling.protocol.v1",)},
    ).actions[0]

    assert action.action_type is CorrectiveActionType.RUN_CONTROLLED_MEASUREMENT
    assert action.priority is CorrectiveActionPriority.REQUIRED_FOR_DISCRIMINATION
    assert action.applicability is CorrectiveActionApplicability.CONDITIONALLY_APPLICABLE


def test_contradictory_reasoning_blocks_correction_and_preserves_contradictions():
    source = reasoning(
        DeterministicReasoningConclusion.CONTRADICTORY_EVIDENCE,
        contradictions=("longitudinal.stable_non_support",),
    )
    action = synthesize(source).actions[0]

    assert action.action_type is CorrectiveActionType.DEFER_ACTION_PENDING_EVIDENCE
    assert action.applicability is CorrectiveActionApplicability.BLOCKED_BY_CONTRADICTION
    assert action.contradictions == ("longitudinal.stable_non_support",)


def test_insufficient_evidence_never_produces_direct_correction():
    action = synthesize(
        reasoning(DeterministicReasoningConclusion.INSUFFICIENT_EVIDENCE)
    ).actions[0]

    assert action.action_type is CorrectiveActionType.DEFER_ACTION_PENDING_EVIDENCE
    assert action.required_missing_parameters == ("additional_supporting_observation",)


def test_already_tested_action_is_not_presented_as_new():
    _, action = supported_with_plan()
    result = synthesize(
        reasoning(),
        plans={"DOMINANT_EARLY_REFLECTION_INTERACTION": ("reflection-plan-001",)},
        tested=(action.action_id,),
    ).actions[0]

    assert result.applicability is CorrectiveActionApplicability.ALREADY_TESTED


def test_invalidated_action_is_blocked_by_history():
    _, action = supported_with_plan()
    result = synthesize(
        reasoning(),
        plans={"DOMINANT_EARLY_REFLECTION_INTERACTION": ("reflection-plan-001",)},
        invalidated=(action.action_id,),
    ).actions[0]

    assert result.applicability is CorrectiveActionApplicability.BLOCKED_BY_HISTORY
    assert "history.invalidated_action" in result.contradictions


def test_existing_protocol_is_structured_parameter_not_free_text():
    source = reasoning(
        DeterministicReasoningConclusion.NON_DISCRIMINATED,
        target="MODAL_BASS_PERSISTENCE",
    )
    action = synthesize(
        source,
        protocols={"MODAL_BASS_PERSISTENCE": ("sampling.protocol.v1",)},
    ).actions[0]

    assert action.known_parameters == (
        ("compatible_protocol_id.1", "sampling.protocol.v1"),
    )


def test_missing_protocol_is_never_silently_invented():
    action = synthesize(
        reasoning(DeterministicReasoningConclusion.NON_DISCRIMINATED)
    ).actions[0]

    assert action.known_parameters == ()
    assert "compatible_protocol_or_plan_id" in action.required_missing_parameters


def test_blocked_campaign_plan_is_not_treated_as_compatible_contract():
    campaign = SimpleNamespace(
        campaign_plan_id="campaign-plan.protocol-unavailable",
        status=ListeningPositionCampaignPlanStatus.BLOCKED,
    )

    assert DeterministicCorrectiveActionStage._plans(
        SimpleNamespace(listening_position_campaign_plan=campaign)
    ) == {}


def test_equivalent_actions_are_deduplicated_and_sources_are_stably_merged():
    first = reasoning(reasoning_id="reasoning.one")
    second = reasoning(reasoning_id="reasoning.two", confidence=60.0)
    result = synthesize(
        first,
        second,
        plans={"DOMINANT_EARLY_REFLECTION_INTERACTION": ("reflection-plan-001",)},
    )

    assert len(result.actions) == 1
    assert result.actions[0].source_reasoning_ids == ("reasoning.one", "reasoning.two")
    assert result.actions[0].confidence == 60.0


def test_action_order_and_identifiers_are_deterministic():
    values = (
        reasoning(reasoning_id="reasoning.early"),
        reasoning(
            DeterministicReasoningConclusion.NON_DISCRIMINATED,
            reasoning_id="reasoning.modal",
            target="MODAL_BASS_PERSISTENCE",
        ),
    )
    first = synthesize(*values)
    second = synthesize(*values)

    assert first == second
    assert tuple(item.action_id for item in first.actions) == (
        "ACTION_RUN_CONTROLLED_MEASUREMENT_DOMINANT_EARLY_REFLECTION_INTERACTION",
        "ACTION_RUN_CONTROLLED_MEASUREMENT_MODAL_BASS_PERSISTENCE",
    )


def test_action_and_collections_are_immutable():
    _, action = supported_with_plan()

    with pytest.raises(FrozenInstanceError):
        action.title = "changed"
    with pytest.raises(TypeError):
        action.source_reasoning_ids[0] = "changed"


def test_action_confidence_never_exceeds_source_reasoning():
    source, action = supported_with_plan(confidence=42.0)

    assert action.confidence == source.confidence
    assert action.confidence <= action.source_confidence_ceiling


def test_no_geometric_or_numeric_parameter_is_invented():
    _, action = supported_with_plan()
    serialized = repr(action.known_parameters).casefold()

    assert "distance" not in serialized
    assert "angle" not in serialized
    assert "gain" not in serialized
    assert "frequency" not in serialized


def test_action_contains_no_hypothesis_or_experiment_creation():
    _, action = supported_with_plan()

    assert not hasattr(action, "new_hypothesis")
    assert not hasattr(action, "experiment")
    assert "does not execute or create an experiment" in action.description


def test_traceability_reaches_reasoning_observation_and_analysis():
    source, action = supported_with_plan()

    assert action.source_reasoning_ids == (source.reasoning_id,)
    assert action.source_observation_ids == source.observation_ids
    assert action.upstream_source_ids == source.upstream_source_ids
    assert action.justifications[0].reasoning_id == source.reasoning_id


def test_invalid_applicable_action_with_missing_parameter_is_rejected():
    _, action = supported_with_plan()

    with pytest.raises(ValueError, match="cannot hide"):
        replace(
            action,
            required_missing_parameters=("invented_required_value",),
        )


def test_empty_action_synthesis_is_valid():
    assert DeterministicCorrectiveActionSynthesis().actions == ()


def test_report_is_byte_for_byte_reproducible_and_non_commercial(capsys):
    _, action = supported_with_plan()
    synthesis = DeterministicCorrectiveActionSynthesis((action,))
    context = SimpleNamespace(deterministic_corrective_action_synthesis=synthesis)
    report = Report(project_name="actions")
    report.deterministic_corrective_actions = (
        DeterministicCorrectiveActionPresenter().present(context)
    )
    reporter = DeterministicCorrectiveActionConsoleReporter()

    reporter.print(report)
    first = capsys.readouterr().out
    reporter.print(report)
    second = capsys.readouterr().out

    assert first == second
    for forbidden in ("achetez", "installez", "meilleur choix", "résoudra le problème"):
        assert forbidden not in first.casefold()


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
        (["--actions"], {"synthesize_actions": True}),
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


def test_engine_is_read_only_for_source_reasoning():
    source = reasoning()
    before = dict(source.__dict__)

    synthesize(source)

    assert source.__dict__ == before
