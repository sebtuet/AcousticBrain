from acousticbrain.analysis.acoustic_hypothesis_experiment_generation import (
    AcousticHypothesisExperimentGenerator,
)


class AcousticHypothesisExperimentGenerationStage:
    def __init__(self, generator=None):
        self.generator = generator or AcousticHypothesisExperimentGenerator()

    def run(self, context):
        context.acoustic_hypothesis_experiment_generation_analysis = (
            self.generator.generate(context)
        )
