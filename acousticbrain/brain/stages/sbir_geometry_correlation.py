from acousticbrain.analysis import SBIRGeometryCorrelationEngine


class SBIRGeometryCorrelationStage:
    def __init__(self, engine=None):
        self.engine = engine or SBIRGeometryCorrelationEngine()

    def run(self, context):
        context.sbir_geometry_correlation_analysis = self.engine.analyze(
            context.geometry_sbir_analysis,
            context.dips,
        )
