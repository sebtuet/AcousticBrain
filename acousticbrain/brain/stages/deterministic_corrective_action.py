from acousticbrain.analysis.deterministic_corrective_action import (
    DeterministicCorrectiveActionEngine,
)
from acousticbrain.models import (
    HypothesisCode,
    ListeningPositionCampaignPlanStatus,
)


class DeterministicCorrectiveActionStage:
    def __init__(self, engine=None):
        self.engine = engine or DeterministicCorrectiveActionEngine()

    def run(self, context):
        context.deterministic_corrective_action_synthesis = self.engine.synthesize(
            context.deterministic_acoustic_reasoning_synthesis,
            protocols_by_target=self._protocols(context),
            plans_by_target=self._plans(context),
            tested_action_ids=tuple(
                getattr(context, "completed_corrective_action_ids", ())
            ),
            invalidated_action_ids=tuple(
                getattr(context, "invalidated_corrective_action_ids", ())
            ),
        )

    @staticmethod
    def _protocols(context):
        values = {}
        sampling = getattr(context, "listening_position_sampling_protocol", None)
        if sampling is not None:
            values[HypothesisCode.MODAL_BASS_PERSISTENCE.value] = (
                sampling.protocol_id,
            )
        causal = getattr(context, "causal_discrimination_analysis", None)
        if causal is not None:
            values[HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION.value] = (
                causal.protocol_code,
            )
        return values

    @staticmethod
    def _plans(context):
        values = {}
        reflection = getattr(
            context, "controlled_reflection_verification_planning_analysis", None
        )
        reflection_ids = tuple(
            item.proposal_id for item in getattr(reflection, "proposals", ())
        )
        if reflection_ids:
            values[
                HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION.value
            ] = reflection_ids
        campaign = getattr(context, "listening_position_campaign_plan", None)
        if (
            campaign is not None
            and campaign.status is ListeningPositionCampaignPlanStatus.READY
        ):
            values[HypothesisCode.MODAL_BASS_PERSISTENCE.value] = (
                campaign.campaign_plan_id,
            )
        return values
