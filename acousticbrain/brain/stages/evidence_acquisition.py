from acousticbrain.analysis import EvidenceAcquisitionPlanner


class EvidenceAcquisitionPlanningStage:
    def __init__(self, planner=None):
        self.planner = planner or EvidenceAcquisitionPlanner()

    def run(self, context):
        context.evidence_acquisition_plan_synthesis = self.planner.plan(
            context.deterministic_acoustic_reasoning_synthesis,
            context.deterministic_corrective_action_synthesis,
            context.deterministic_evidence_weighting_synthesis,
        )
