from acousticbrain.analysis import GeometrySBIRPredictionEngine


class GeometrySBIRStage:
    def __init__(self, engine=None):
        self.engine = engine or GeometrySBIRPredictionEngine()

    def run(self, context):
        context.geometry_sbir_analysis = self.engine.analyze(
            context.geometry_early_reflection_analysis,
            context.room_geometry,
        )
