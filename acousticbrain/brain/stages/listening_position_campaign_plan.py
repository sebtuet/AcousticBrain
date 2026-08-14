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
        instance_analysis = getattr(
            context, "listening_position_campaign_instance_analysis", None
        )
        experiments = tuple(
            replace(
                item,
                blocking_reasons=tuple(
                    dict.fromkeys(
                        (
                            *(
                                reason
                                for reason in item.blocking_reasons
                                if not (
                                    instance_analysis is not None
                                    and reason
                                    == "MULTI_POSITION_SAMPLING_GEOMETRY_UNAVAILABLE"
                                )
                            ),
                            *plan.blocking_reasons,
                        )
                    )
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
