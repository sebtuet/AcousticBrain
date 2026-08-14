from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.direct_reverberant_correlation import (
    DirectReverberantCorrelationStage,
)
from acousticbrain.models import (
    ClarityAnalysis,
    DirectReverberantAnalysis,
    DirectReverberantCorrelationAnalysis,
    ETCAnalysis,
    Measurement,
    RT60Analysis,
    SpatialAnalysis,
)


class RecordingEngine:
    def __init__(self):
        self.inputs = None
        self.result = DirectReverberantCorrelationAnalysis()

    def correlate(self, *inputs):
        self.inputs = inputs
        return self.result


def test_stage_only_delegates_structured_analyses():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.direct_reverberant_analysis = DirectReverberantAnalysis()
    context.rt60_analysis = RT60Analysis()
    context.etc_analysis = ETCAnalysis()
    context.clarity_analysis = ClarityAnalysis()
    context.spatial_analysis = SpatialAnalysis()
    engine = RecordingEngine()

    DirectReverberantCorrelationStage(engine).run(context)

    assert engine.inputs == (
        context.direct_reverberant_analysis,
        context.rt60_analysis,
        context.etc_analysis,
        context.clarity_analysis,
        context.spatial_analysis,
    )
    assert context.direct_reverberant_correlation_analysis is engine.result
