from acousticbrain.analysis import ControlledReflectionVerificationPlanningEngine


class ControlledReflectionVerificationPlanningStage:
    """Publishes a descriptive leaf analysis from PR-035 candidates only."""

    def __init__(self, engine=None):
        self.engine = engine or ControlledReflectionVerificationPlanningEngine()

    def run(self, context):
        context.controlled_reflection_verification_planning_analysis = (
            self.engine.analyze(
                context.material_aware_reflection_candidate_analysis
            )
        )
