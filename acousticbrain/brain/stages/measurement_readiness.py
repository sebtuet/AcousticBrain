from acousticbrain.analysis import MeasurementReadinessEngine


class MeasurementReadinessStage:
    """Produit la readiness sans contrôler l'exécution du pipeline."""

    def __init__(self, engine=None):
        self.engine = engine or MeasurementReadinessEngine()

    def run(self, context):
        context.measurement_readiness_analysis = self.engine.analyze(
            context.measurement_quality_analysis
        )
