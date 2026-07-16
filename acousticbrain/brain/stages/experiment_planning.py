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
            completed_protocol_ids=self._completed_protocol_ids(
                context.experiment_descriptors
            ),
            causal_discrimination_analysis=getattr(
                context, "causal_discrimination_analysis", None
            ),
            generated_experiment_analysis=getattr(
                context,
                "acoustic_hypothesis_experiment_generation_analysis",
                None,
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

    @staticmethod
    def _completed_protocol_ids(descriptors):
        completion_changes = {
            "protocol.verify_modal_bass_persistence.v1": (
                "MULTIPLE_LISTENING_POSITIONS"
            ),
            "protocol.temporary_move_speaker.v1": "TEMPORARY_SPEAKER_MOVE",
        }
        return tuple(dict.fromkeys(
            descriptor.source_protocol_id
            for descriptor in descriptors
            if descriptor.source_protocol_id is not None
            and completion_changes.get(descriptor.source_protocol_id)
            in descriptor.declared_change_codes
        ))
