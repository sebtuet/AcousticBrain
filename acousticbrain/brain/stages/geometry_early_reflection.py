from acousticbrain.analysis import GeometryEarlyReflectionEngine


class GeometryEarlyReflectionStage:
    def __init__(self, engine=None):
        self.engine = engine or GeometryEarlyReflectionEngine()

    def run(self, context):
        context.geometry_early_reflection_analysis = self.engine.analyze(
            context.propagation_geometry
        )
