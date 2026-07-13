from acousticbrain.analysis import AnalysisContext, AcousticReasoningEngine
from acousticbrain.brain.stages.experiment_planning import ExperimentPlanningStage
from acousticbrain.models import Measurement


class RecordingPlanner:
    def __init__(self):
        self.arguments = None
        self.result = object()

    def plan(self, reasoning, *, session=None):
        self.arguments = (reasoning, session)
        return self.result


def test_stage_maps_reasoning_and_optional_session_without_side_effects():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.acoustic_reasoning_analysis = AcousticReasoningEngine().analyze()
    session = object()
    planner = RecordingPlanner()

    ExperimentPlanningStage(planner).run(context, session=session)

    assert planner.arguments == (context.acoustic_reasoning_analysis, session)
    assert context.experiment_planning_analysis is planner.result
