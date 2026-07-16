from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from acousticbrain.analysis.listening_position_campaign_plan import (
    ListeningPositionCampaignPlanBuilder,
)
from acousticbrain.brain import AcousticBrain
from acousticbrain.brain.stages.acoustic_hypothesis_experiment_generation import (
    AcousticHypothesisExperimentGenerationStage,
)
from acousticbrain.brain.stages.listening_position_campaign_plan import (
    ListeningPositionCampaignPlanStage,
)
from acousticbrain.brain.stages.experiment_planning import ExperimentPlanningStage
from acousticbrain.models import (
    ComparisonEligibilityStatus,
    ExperimentKind,
    ExperimentState,
    ImpulseChannel,
    ListeningPositionCampaignPlanStatus,
    ListeningPositionSamplingProtocol,
    ExperimentPlanningStatus,
)
from acousticbrain.report import (
    AcousticHypothesisExperimentGenerationPresenter,
    ConsoleReporter,
    ListeningPositionCampaignPlanPresenter,
    Report,
)
from test_acoustic_hypothesis_experiment_generation import (
    modal_context,
    sampling_protocol,
)
from test_golden_report import reference_project


def structured_reference(protocol, experiment_id="exp-007"):
    return SimpleNamespace(
        experiment_id=experiment_id,
        state=ExperimentState.READY,
        available_channels=(
            ImpulseChannel.LEFT,
            ImpulseChannel.RIGHT,
            ImpulseChannel.STEREO,
        ),
        experiment_declaration=SimpleNamespace(
            experiment_kind=ExperimentKind.CONTROLLED_INTERVENTION,
            modified_variables=("PREVIOUS_CONTROLLED_CHANGE",),
            controlled_variables=protocol.controlled_variables,
        ),
    )


def comparable_sequence(experiment_id="exp-007"):
    return SimpleNamespace(
        sequence=SimpleNamespace(
            chronology=("exp-006", experiment_id),
            local_comparisons=(
                SimpleNamespace(
                    after_experiment_id=experiment_id,
                    eligibility=ComparisonEligibilityStatus.COMPARABLE,
                ),
            ),
        )
    )


def campaign_context(*, protocol=None, reference=True):
    protocol = protocol or sampling_protocol()
    value = modal_context(with_sampling_geometry=False)
    value.listening_position_sampling_protocol = protocol
    AcousticHypothesisExperimentGenerationStage().run(value)
    value.experiment_descriptors = (
        (structured_reference(protocol),) if reference else ()
    )
    value.experiment_comparison_analysis = (
        comparable_sequence() if reference else None
    )
    return value


def build_ready_context():
    value = campaign_context()
    ListeningPositionCampaignPlanStage().run(value)
    return value


def test_complete_protocol_and_admissible_reference_produce_ready_plan():
    value = build_ready_context()
    plan = value.listening_position_campaign_plan

    assert plan.status is ListeningPositionCampaignPlanStatus.READY
    assert plan.reference_experiment_id == "exp-007"
    assert plan.protocol_id == sampling_protocol().protocol_id
    assert plan.blocking_reasons == ()
    assert plan.source_candidate_id.startswith("generated.")
    assert plan.source_hypothesis_code == "MODAL_BASS_PERSISTENCE"


def test_incomplete_protocol_produces_visible_blocked_plan():
    complete = sampling_protocol()
    incomplete = replace(complete, positions=complete.positions[:2])
    value = campaign_context(protocol=incomplete, reference=False)

    plan = ListeningPositionCampaignPlanBuilder().build(value)

    assert plan.status is ListeningPositionCampaignPlanStatus.BLOCKED
    assert "MULTI_POSITION_SAMPLING_GEOMETRY_UNAVAILABLE" in plan.blocking_reasons
    assert plan.steps == ()


def test_absent_reference_is_not_invented_and_blocks_plan():
    plan = ListeningPositionCampaignPlanBuilder().build(
        campaign_context(reference=False)
    )

    assert plan.status is ListeningPositionCampaignPlanStatus.BLOCKED
    assert plan.reference_experiment_id is None
    assert plan.blocking_reasons == (
        "CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE",
    )


@pytest.mark.parametrize(
    ("channels", "kind", "eligibility"),
    (
        (
            (ImpulseChannel.LEFT, ImpulseChannel.RIGHT),
            ExperimentKind.CONTROLLED_INTERVENTION,
            ComparisonEligibilityStatus.COMPARABLE,
        ),
        (
            (ImpulseChannel.LEFT, ImpulseChannel.RIGHT, ImpulseChannel.STEREO),
            ExperimentKind.UNKNOWN,
            ComparisonEligibilityStatus.COMPARABLE,
        ),
        (
            (ImpulseChannel.LEFT, ImpulseChannel.RIGHT, ImpulseChannel.STEREO),
            ExperimentKind.CONTROLLED_INTERVENTION,
            ComparisonEligibilityStatus.NOT_COMPARABLE,
        ),
    ),
)
def test_reference_requires_measurements_declaration_and_comparability(
    channels, kind, eligibility
):
    value = campaign_context(reference=False)
    protocol = value.listening_position_sampling_protocol
    descriptor = structured_reference(protocol)
    descriptor.available_channels = channels
    descriptor.experiment_declaration.experiment_kind = kind
    value.experiment_descriptors = (descriptor,)
    value.experiment_comparison_analysis = comparable_sequence()
    value.experiment_comparison_analysis.sequence.local_comparisons[
        0
    ].eligibility = eligibility

    plan = ListeningPositionCampaignPlanBuilder().build(value)

    assert plan.status is ListeningPositionCampaignPlanStatus.BLOCKED
    assert plan.reference_experiment_id is None
    assert plan.blocking_reasons == (
        "CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE",
    )


def test_latest_admissible_reference_is_selected_not_latest_descriptor_blindly():
    value = campaign_context(reference=False)
    protocol = value.listening_position_sampling_protocol
    admissible = structured_reference(protocol, "exp-007")
    latest_unknown = structured_reference(protocol, "exp-008")
    latest_unknown.experiment_declaration.experiment_kind = ExperimentKind.UNKNOWN
    value.experiment_descriptors = (admissible, latest_unknown)
    value.experiment_comparison_analysis = SimpleNamespace(
        sequence=SimpleNamespace(
            chronology=("exp-006", "exp-007", "exp-008"),
            local_comparisons=(
                SimpleNamespace(
                    after_experiment_id="exp-007",
                    eligibility=ComparisonEligibilityStatus.COMPARABLE,
                ),
                SimpleNamespace(
                    after_experiment_id="exp-008",
                    eligibility=ComparisonEligibilityStatus.COMPARABLE,
                ),
            ),
        )
    )

    plan = ListeningPositionCampaignPlanBuilder().build(value)

    assert plan.status is ListeningPositionCampaignPlanStatus.READY
    assert plan.reference_experiment_id == "exp-007"


def test_reference_without_declared_configuration_coverage_is_rejected():
    value = campaign_context(reference=False)
    protocol = value.listening_position_sampling_protocol
    descriptor = structured_reference(protocol)
    descriptor.experiment_declaration.controlled_variables = (
        protocol.controlled_variables[:-1]
    )
    value.experiment_descriptors = (descriptor,)
    value.experiment_comparison_analysis = comparable_sequence()

    plan = ListeningPositionCampaignPlanBuilder().build(value)

    assert plan.status is ListeningPositionCampaignPlanStatus.BLOCKED
    assert plan.blocking_reasons == (
        "CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE",
    )


def test_ineligible_source_candidate_never_produces_ready_plan():
    value = campaign_context()
    analysis = value.acoustic_hypothesis_experiment_generation_analysis
    candidate = analysis.ordered_experiments[0]
    value.acoustic_hypothesis_experiment_generation_analysis = replace(
        analysis,
        ordered_experiments=(
            replace(candidate, blocking_reasons=("TEST_SOURCE_BLOCK",)),
        ),
        recommended_candidate_id=None,
    )

    plan = ListeningPositionCampaignPlanBuilder().build(value)

    assert plan.status is ListeningPositionCampaignPlanStatus.BLOCKED
    assert "SOURCE_CANDIDATE_NOT_ELIGIBLE" in plan.blocking_reasons


def test_missing_candidate_measurement_uses_specific_plan_blocking_reason():
    value = campaign_context()
    analysis = value.acoustic_hypothesis_experiment_generation_analysis
    candidate = analysis.ordered_experiments[0]
    value.acoustic_hypothesis_experiment_generation_analysis = replace(
        analysis,
        ordered_experiments=(
            replace(
                candidate,
                blocking_reasons=("REQUIRED_MEASUREMENT_UNAVAILABLE:LEFT",),
            ),
        ),
        recommended_candidate_id=None,
    )

    plan = ListeningPositionCampaignPlanBuilder().build(value)

    assert plan.status is ListeningPositionCampaignPlanStatus.BLOCKED
    assert plan.blocking_reasons == ("REQUIRED_MEASUREMENTS_UNAVAILABLE",)


def test_step_order_offsets_and_relations_are_projected_exactly():
    protocol = sampling_protocol()
    plan = build_ready_context().listening_position_campaign_plan

    assert tuple(item.position_code for item in plan.steps) == tuple(
        item.position_code for item in protocol.positions
    )
    assert tuple(item.order_index for item in plan.steps) == tuple(
        item.acquisition_order for item in protocol.positions
    )
    assert tuple(item.longitudinal_offset_m for item in plan.steps) == tuple(
        item.longitudinal_offset_m for item in protocol.positions
    )
    assert tuple(item.lateral_offset_m for item in plan.steps) == (None, None, None)
    assert tuple(item.vertical_offset_m for item in plan.steps) == (None, None, None)
    assert tuple(item.parent_step_id for item in plan.steps) == (
        None,
        "campaign-step.REFERENCE",
        "campaign-step.FORWARD_100MM",
    )
    assert tuple(item.reference_step_id for item in plan.steps) == (
        "campaign-step.REFERENCE",
        "campaign-step.REFERENCE",
        "campaign-step.REFERENCE",
    )


def test_invalid_or_cyclic_parent_relation_is_rejected():
    plan = build_ready_context().listening_position_campaign_plan
    invalid_steps = (
        plan.steps[0],
        replace(plan.steps[1], parent_step_id=plan.steps[2].step_id),
        plan.steps[2],
    )

    with pytest.raises(ValueError, match="invalid or cyclic"):
        replace(plan, steps=invalid_steps)


def test_every_step_requires_left_right_and_stereo_and_exact_controls():
    plan = build_ready_context().listening_position_campaign_plan

    assert all(
        item.required_measurements == ("LEFT", "RIGHT", "STEREO")
        for item in plan.steps
    )
    assert all(
        item.controlled_variables == plan.controlled_variables
        for item in plan.steps
    )


def test_plan_invents_no_future_experiment_identity():
    plan = build_ready_context().listening_position_campaign_plan

    assert plan.reference_experiment_id == "exp-007"
    assert all(not item.step_id.startswith("exp-") for item in plan.steps)
    assert "exp-008" not in repr(plan)
    assert "exp-009" not in repr(plan)
    assert "exp-010" not in repr(plan)


def test_builder_writes_nothing_and_does_not_change_cwd(tmp_path):
    before_cwd = Path.cwd()
    before_files = tuple(tmp_path.rglob("*"))

    plan = ListeningPositionCampaignPlanBuilder().build(campaign_context())

    assert plan.status is ListeningPositionCampaignPlanStatus.READY
    assert Path.cwd() == before_cwd
    assert tuple(tmp_path.rglob("*")) == before_files


def test_builder_does_not_mutate_protocol_candidate_or_source_history():
    value = campaign_context()
    before_protocol = deepcopy(value.listening_position_sampling_protocol)
    before_generation = deepcopy(
        value.acoustic_hypothesis_experiment_generation_analysis
    )
    before_descriptors = deepcopy(value.experiment_descriptors)
    before_comparison = deepcopy(value.experiment_comparison_analysis)

    ListeningPositionCampaignPlanBuilder().build(value)

    assert value.listening_position_sampling_protocol == before_protocol
    assert value.acoustic_hypothesis_experiment_generation_analysis == before_generation
    assert value.experiment_descriptors == before_descriptors
    assert value.experiment_comparison_analysis == before_comparison


def test_ready_report_distinguishes_candidate_protocol_plan_and_future_steps(capsys):
    value = build_ready_context()
    report = Report(project_name="campaign-plan")
    report.acoustic_hypothesis_experiment_generation = (
        AcousticHypothesisExperimentGenerationPresenter().present(value)
    )
    report.listening_position_campaign_plan = (
        ListeningPositionCampaignPlanPresenter().present(value)
    )

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert "Candidat expérimental : LISTENING_POSITION_MULTI_POINT" in output
    assert "Protocole multi-position structuré" in output
    assert "PLAN DE CAMPAGNE MULTI-POSITION" in output
    assert "Statut : READY" in output
    assert "Référence existante : exp-007" in output
    assert "Identifiant interne : campaign-step.REFERENCE" in output
    assert "Aucune expérience ni aucun fichier n’a encore été créé." in output
    assert output.count("Expérience principale\n") == 1


def test_blocked_report_is_readable_and_candidate_is_never_main(capsys):
    value = campaign_context(reference=False)
    ListeningPositionCampaignPlanStage().run(value)
    report = Report(project_name="blocked-campaign-plan")
    report.acoustic_hypothesis_experiment_generation = (
        AcousticHypothesisExperimentGenerationPresenter().present(value)
    )
    report.listening_position_campaign_plan = (
        ListeningPositionCampaignPlanPresenter().present(value)
    )

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert "Aucune expérience principale directement exécutable" in output
    assert "PLAN DE CAMPAGNE MULTI-POSITION" in output
    assert "Statut : BLOCKED" in output
    assert "CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE" in output
    assert "Expérience principale\nType : LISTENING_POSITION_MULTI_POINT" not in output


def test_blocked_plan_keeps_legacy_planner_without_eligible_candidate():
    value = campaign_context(reference=False)
    ListeningPositionCampaignPlanStage().run(value)

    ExperimentPlanningStage().run(value)

    assert (
        value.experiment_planning_analysis.status
        is ExperimentPlanningStatus.NO_ELIGIBLE_CANDIDATE
    )


def test_presented_projection_is_stable():
    value = build_ready_context()
    presenter = ListeningPositionCampaignPlanPresenter()

    assert presenter.present(value).to_dict() == presenter.present(value).to_dict()


def test_campaign_plan_preserves_all_existing_scientific_outputs():
    project = reference_project()
    baseline = AcousticBrain().analyze(project)
    enriched = AcousticBrain().analyze(
        project,
        listening_position_sampling_protocol=sampling_protocol(),
    )

    assert enriched.global_analysis == baseline.global_analysis
    assert enriched.recommendations == baseline.recommendations
    assert enriched.causal_discrimination == baseline.causal_discrimination
    assert (
        enriched.longitudinal_experimental_learning
        == baseline.longitudinal_experimental_learning
    )
    baseline_hypotheses = tuple(
        item.hypothesis_code
        for item in baseline.acoustic_hypothesis_experiment_generation.hypotheses
    )
    enriched_hypotheses = tuple(
        item.hypothesis_code
        for item in enriched.acoustic_hypothesis_experiment_generation.hypotheses
    )
    assert enriched_hypotheses == baseline_hypotheses
