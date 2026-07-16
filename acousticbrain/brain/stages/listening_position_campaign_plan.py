from dataclasses import replace

from acousticbrain.analysis.listening_position_campaign_plan import (
    ListeningPositionCampaignPlanBuilder,
)
from acousticbrain.models import ListeningPositionCampaignPlanStatus


class ListeningPositionCampaignPlanStage:
    def __init__(self, builder=None):
        self.builder = builder or ListeningPositionCampaignPlanBuilder()

    def run(self, context):
        plan = self.builder.build(context)
        context.listening_position_campaign_plan = plan
        if plan is None or plan.status is ListeningPositionCampaignPlanStatus.READY:
            return

        analysis = context.acoustic_hypothesis_experiment_generation_analysis
        experiments = tuple(
            replace(
                item,
                blocking_reasons=tuple(
                    dict.fromkeys((*item.blocking_reasons, *plan.blocking_reasons))
                ),
            )
            if item.candidate_id == plan.source_candidate_id
            else item
            for item in analysis.ordered_experiments
        )
        recommended = next(
            (item.candidate_id for item in experiments if item.eligible), None
        )
        context.acoustic_hypothesis_experiment_generation_analysis = replace(
            analysis,
            ordered_experiments=experiments,
            recommended_candidate_id=recommended,
        )
