from acousticbrain.analysis import ExperimentPlanner


class ExperimentPlanningStage:
    """Orchestre uniquement la planification explicitement demandée."""

    def __init__(self, planner=None):
        self.planner = planner or ExperimentPlanner()

    def run(self, context, *, session=None):
        context.experiment_planning_analysis = self.planner.plan(
            context.acoustic_reasoning_analysis,
            session=session,
        )
