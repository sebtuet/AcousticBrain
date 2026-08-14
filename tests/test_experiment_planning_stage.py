from types import SimpleNamespace

from acousticbrain.analysis import AnalysisContext, AcousticReasoningEngine
from acousticbrain.brain.stages.experiment_planning import ExperimentPlanningStage
from acousticbrain.models import (
    CausalDiscriminationOutcome,
    ExperimentSelectionReason,
    HypothesisCode,
    Measurement,
)


class RecordingPlanner:
    def __init__(self):
        self.arguments = None
        self.result = object()

    def plan(
        self,
        reasoning,
        *,
        session=None,
        deferred_action_codes=(),
        completed_protocol_ids=(),
        causal_discrimination_analysis=None,
        generated_experiment_analysis=None,
        movement_direction_declarations=(),
    ):
        self.arguments = (
            reasoning,
            session,
            deferred_action_codes,
            completed_protocol_ids,
            causal_discrimination_analysis,
            generated_experiment_analysis,
            movement_direction_declarations,
        )
        return self.result


def test_stage_maps_reasoning_and_optional_session_without_side_effects():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.acoustic_reasoning_analysis = AcousticReasoningEngine().analyze()
    session = object()
    planner = RecordingPlanner()

    ExperimentPlanningStage(planner).run(context, session=session)

    assert planner.arguments == (
        context.acoustic_reasoning_analysis,
        session,
        (),
        (),
        None,
        None,
        (),
    )
    assert context.experiment_planning_analysis is planner.result


def test_stage_closes_declared_temporary_speaker_move_protocol():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.acoustic_reasoning_analysis = AcousticReasoningEngine().analyze()
    context.experiment_descriptors = (SimpleNamespace(
        source_protocol_id="protocol.temporary_move_speaker.v1",
        declared_change_codes=("TEMPORARY_SPEAKER_MOVE",),
        causal_discrimination_decisions=(),
    ),)
    planner = RecordingPlanner()

    ExperimentPlanningStage(planner).run(context)

    assert planner.arguments[3] == ("protocol.temporary_move_speaker.v1",)


def test_stage_excludes_discriminated_causal_protocol_after_step_2_and_step_3():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.acoustic_reasoning_analysis = AcousticReasoningEngine().analyze()
    context.causal_discrimination_analysis = SimpleNamespace(
        protocol_code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
        outcome=CausalDiscriminationOutcome.DISCRIMINATED,
        completed_steps=(
            SimpleNamespace(step_code="STEP_2_SPEAKER_SWAP"),
            SimpleNamespace(step_code="STEP_3_SIGNAL_CHAIN_SWAP"),
        ),
        remaining_discrimination_codes=(),
        recommended_next_protocol=None,
    )

    ExperimentPlanningStage().run(context)

    candidates = (
        *context.experiment_planning_analysis.plan.ordered_candidates,
        *context.experiment_planning_analysis.plan.ineligible_candidates,
    )
    asymmetry = next(
        item
        for item in candidates
        if item.hypothesis_code
        == HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION.value
    )
    assert asymmetry.eligible is False
    assert ExperimentSelectionReason.CAUSAL_DISCRIMINATION_COMPLETED in (
        asymmetry.ineligibility_reasons
    )
    assert context.experiment_planning_analysis.plan.recommended_candidate is not asymmetry
