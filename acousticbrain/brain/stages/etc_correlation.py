from acousticbrain.analysis import ETCReflectionCorrelationEngine


class ETCCorrelationStage:
    """Orchestre le rapprochement des analyses ETC et SBIR existantes."""

    def __init__(self, engine=None):
        self.engine = engine or ETCReflectionCorrelationEngine()

    def run(self, context):
        context.etc_reflection_correlation_analysis = self.engine.analyze(
            context.etc_analysis,
            context.sbir,
            geometry_reflections=context.geometry_early_reflection_analysis,
        )
