from acousticbrain.analysis import ClarityCorrelationEngine


class ClarityCorrelationStage:
    """Orchestre le croisement d'analyses temporelles déjà produites."""

    def __init__(self, engine=None):
        self.engine = engine or ClarityCorrelationEngine()

    def run(self, context):
        context.clarity_correlation_analysis = self.engine.correlate(
            context.clarity_analysis,
            context.rt60_analysis,
            context.etc_analysis,
        )
