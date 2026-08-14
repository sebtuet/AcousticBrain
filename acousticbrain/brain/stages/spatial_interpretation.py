from acousticbrain.analysis import (
    SpatialCorrelationEngine,
    SpatialInterpretationEngine,
)


class SpatialInterpretationStage:
    """Orchestre l'interprétation et les corrélations spatiales existantes."""

    def __init__(self, interpreter=None, correlator=None):
        self.interpreter = interpreter or SpatialInterpretationEngine()
        self.correlator = correlator or SpatialCorrelationEngine()

    def run(self, context):
        context.spatial_interpretation = self.interpreter.interpret(
            context.spatial_analysis
        )
        context.spatial_correlation_analysis = self.correlator.correlate(
            context.spatial_analysis,
            context.spatial_interpretation,
            context.stereo,
            context.etc_analysis,
            context.clarity_analysis,
        )
