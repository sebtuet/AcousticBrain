from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.etc_correlation import ETCCorrelationStage
from acousticbrain.models import (
    ETCAnalysis,
    ETCReflectionCorrelationAnalysis,
    Measurement,
)


class RecordingEngine:
    def __init__(self):
        self.inputs = None
        self.result = ETCReflectionCorrelationAnalysis()

    def analyze(self, etc_analysis, sbir_analysis):
        self.inputs = (etc_analysis, sbir_analysis)
        return self.result


def test_etc_correlation_stage_only_delegates_existing_analyses():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.etc_analysis = ETCAnalysis()
    context.sbir = object()
    engine = RecordingEngine()

    ETCCorrelationStage(engine).run(context)

    assert engine.inputs == (context.etc_analysis, context.sbir)
    assert context.etc_reflection_correlation_analysis is engine.result

