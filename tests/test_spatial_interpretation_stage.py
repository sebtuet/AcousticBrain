from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.spatial_interpretation import (
    SpatialInterpretationStage,
)
from acousticbrain.models import (
    ClarityAnalysis,
    ETCAnalysis,
    Measurement,
    SpatialAnalysis,
    SpatialCorrelationAnalysis,
    StereoAnalysis,
)


class Interpreter:
    def __init__(self):
        self.input = None
        self.result = object()

    def interpret(self, analysis):
        self.input = analysis
        return self.result


class Correlator:
    def __init__(self):
        self.inputs = None
        self.result = SpatialCorrelationAnalysis()

    def correlate(self, *inputs):
        self.inputs = inputs
        return self.result


def test_stage_only_delegates_structured_analyses():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.spatial_analysis = SpatialAnalysis()
    context.stereo = StereoAnalysis()
    context.etc_analysis = ETCAnalysis()
    context.clarity_analysis = ClarityAnalysis()
    interpreter = Interpreter()
    correlator = Correlator()

    SpatialInterpretationStage(interpreter, correlator).run(context)

    assert interpreter.input is context.spatial_analysis
    assert correlator.inputs == (
        context.spatial_analysis,
        interpreter.result,
        context.stereo,
        context.etc_analysis,
        context.clarity_analysis,
    )
    assert context.spatial_correlation_analysis is correlator.result
