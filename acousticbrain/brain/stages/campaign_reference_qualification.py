from acousticbrain.analysis.campaign_reference_qualification import (
    CampaignReferenceQualificationBuilder,
)


class CampaignReferenceQualificationStage:
    def __init__(self, builder=None):
        self.builder = builder or CampaignReferenceQualificationBuilder()

    def run(self, context):
        context.campaign_reference_qualification = self.builder.build(context)
