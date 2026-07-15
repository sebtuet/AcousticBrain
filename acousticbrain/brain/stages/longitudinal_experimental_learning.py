from acousticbrain.analysis import LongitudinalExperimentalLearningEngine


class LongitudinalExperimentalLearningStage:
    """Dérive l'état longitudinal après comparaisons et discriminations."""

    def __init__(self, engine=None):
        self.engine = engine or LongitudinalExperimentalLearningEngine()

    def run(self, context):
        context.longitudinal_experimental_learning_analysis = self.engine.analyze(
            descriptors=context.experiment_descriptors,
            comparison_analysis=context.experiment_comparison_analysis,
            campaign_analyses=context.experiment_campaign_analyses,
            causal_discrimination=context.causal_discrimination_analysis,
            acoustic_reasoning=context.acoustic_reasoning_analysis,
        )
