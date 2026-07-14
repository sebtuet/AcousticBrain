from types import SimpleNamespace

from acousticbrain.analysis import AnalysisContext, AcousticReasoningEngine
from acousticbrain.brain.stages.experiment_planning import ExperimentPlanningStage
from acousticbrain.models import Measurement


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
    ):
        self.arguments = (
            reasoning,
            session,
            deferred_action_codes,
            completed_protocol_ids,
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
