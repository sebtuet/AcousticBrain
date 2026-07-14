from acousticbrain.analysis import ExperimentPlanner
from acousticbrain.models import CausalDiscriminationDecisionStatus


class ExperimentPlanningStage:
    """Orchestre uniquement la planification explicitement demandée."""

    def __init__(self, planner=None):
        self.planner = planner or ExperimentPlanner()

    def run(self, context, *, session=None):
        context.experiment_planning_analysis = self.planner.plan(
            context.acoustic_reasoning_analysis,
            session=session,
            deferred_action_codes=self._deferred_action_codes(
                context.experiment_descriptors
            ),
        )

    @staticmethod
    def _deferred_action_codes(descriptors):
        action_by_discrimination = {
            "LOUDSPEAKER_VS_ROOM_SIDE": "VERIFY_SPEAKER_ROOM_ASYMMETRY",
        }
        return tuple(dict.fromkeys(
            action_by_discrimination[item.discrimination_code]
            for descriptor in descriptors
            for item in descriptor.causal_discrimination_decisions
            if item.status is CausalDiscriminationDecisionStatus.DEFERRED
            and item.discrimination_code in action_by_discrimination
        ))
