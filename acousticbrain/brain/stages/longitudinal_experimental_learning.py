from acousticbrain.analysis import LongitudinalExperimentalLearningEngine


class LongitudinalExperimentalLearningStage:
    """Dérive l'état longitudinal après comparaisons et discriminations."""

    def __init__(self, engine=None):
        self.engine = engine or LongitudinalExperimentalLearningEngine()

    def run(self, context):
        context.longitudinal_experimental_learning_analysis = self.engine.analyze(
            descriptors=getattr(context, "experiment_descriptors", ()),
            comparison_analysis=getattr(
                context,
                "experiment_comparison_analysis",
                None,
            ),
            campaign_analyses=getattr(
                context,
                "experiment_campaign_analyses",
                (),
            ),
            causal_discrimination=getattr(
                context,
                "causal_discrimination_analysis",
                None,
            ),
            acoustic_reasoning=getattr(
                context,
                "acoustic_reasoning_analysis",
                None,
            ),
        )
