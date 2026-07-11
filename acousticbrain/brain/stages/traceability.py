from acousticbrain.analysis import TraceabilityEngine


class TraceabilityStage:
    """Orchestre la traçabilité lorsque ses connaissances sont disponibles."""

    def __init__(self, engine=None):
        self.engine = engine or TraceabilityEngine()

    def run(self, context):
        context.traceability_analysis = self.engine.analyze(
            global_analysis=context.global_analysis,
            recommendation_analysis=context.recommendation_analysis,
            confidence=getattr(context, "confidence_analysis", None),
        )
