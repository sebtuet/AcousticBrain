from acousticbrain.analysis.deterministic_acoustic_reasoning import (
    DeterministicAcousticReasoningEngine,
)


class DeterministicAcousticReasoningStage:
    def __init__(self, engine=None):
        self.engine = engine or DeterministicAcousticReasoningEngine()

    def run(self, context):
        context.deterministic_acoustic_reasoning_synthesis = self.engine.synthesize(
            context.acoustic_observation_synthesis,
            acoustic_reasoning=getattr(context, "acoustic_reasoning_analysis", None),
            causal_discrimination=getattr(
                context, "causal_discrimination_analysis", None
            ),
            longitudinal_learning=getattr(
                context, "longitudinal_experimental_learning_analysis", None
            ),
        )
