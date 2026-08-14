from acousticbrain.analysis import DirectReverberantCorrelationEngine


class DirectReverberantCorrelationStage:
    """Orchestre uniquement le croisement d'analyses déjà produites."""

    def __init__(self, engine=None):
        self.engine = engine or DirectReverberantCorrelationEngine()

    def run(self, context):
        context.direct_reverberant_correlation_analysis = (
            self.engine.correlate(
                context.direct_reverberant_analysis,
                context.rt60_analysis,
                context.etc_analysis,
                context.clarity_analysis,
                context.spatial_analysis,
            )
        )
