from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.sbir_geometry_correlation import (
    SBIRGeometryCorrelationStage,
)
from acousticbrain.models import Measurement


class RecordingEngine:
    def __init__(self):
        self.inputs = None
        self.result = object()

    def analyze(self, predictions, dips):
        self.inputs = (predictions, dips)
        return self.result


def test_sbir_correlation_stage_only_delegates_predictions_and_observations():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.geometry_sbir_analysis = object()
    context.dips = [object()]
    engine = RecordingEngine()

    SBIRGeometryCorrelationStage(engine).run(context)

    assert engine.inputs == (context.geometry_sbir_analysis, context.dips)
    assert context.sbir_geometry_correlation_analysis is engine.result
