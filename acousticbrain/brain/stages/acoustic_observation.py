from acousticbrain.analysis.acoustic_observation import (
    DeterministicAcousticObservationSynthesizer,
)


class AcousticObservationStage:
    def __init__(self, synthesizer=None):
        self.synthesizer = synthesizer or DeterministicAcousticObservationSynthesizer()

    def run(self, context):
        context.acoustic_observation_synthesis = self.synthesizer.synthesize(context)
