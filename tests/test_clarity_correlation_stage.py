from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.clarity_correlation import ClarityCorrelationStage
from acousticbrain.models import (
    ClarityAnalysis,
    ClarityCorrelationAnalysis,
    ETCAnalysis,
    Measurement,
    RT60Analysis,
)


class RecordingEngine:
    def __init__(self):
        self.inputs = None
        self.result = ClarityCorrelationAnalysis()

    def correlate(self, clarity, rt60, etc):
        self.inputs = (clarity, rt60, etc)
        return self.result


def test_stage_only_delegates_existing_structured_analyses():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.clarity_analysis = ClarityAnalysis()
    context.rt60_analysis = RT60Analysis()
    context.etc_analysis = ETCAnalysis()
    engine = RecordingEngine()

    ClarityCorrelationStage(engine).run(context)

    assert engine.inputs == (
        context.clarity_analysis,
        context.rt60_analysis,
        context.etc_analysis,
    )
    assert context.clarity_correlation_analysis is engine.result
