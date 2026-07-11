from acousticbrain.analysis import RecommendationEngine


class RecommendationStage:
    """Orchestre le moteur une fois toutes les analyses disponibles."""

    def __init__(self, engine=None):
        self.engine = engine or RecommendationEngine()

    def run(self, context):
        context.recommendation_analysis = self.engine.analyze(
            stereo=context.stereo,
            sbir=context.sbir,
            modal_density=context.modal_density,
            peak_classification=getattr(context, "peak_classification", None),
            confidence=getattr(context, "confidence_analysis", None),
        )

