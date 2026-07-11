from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.traceability import TraceabilityStage
from acousticbrain.models import Measurement, TraceabilityAnalysis


class RecordingEngine:
    def __init__(self):
        self.inputs = None
        self.result = TraceabilityAnalysis()

    def analyze(self, **inputs):
        self.inputs = inputs
        return self.result


def test_traceability_stage_stores_result_from_explicit_knowledge_layers():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.global_analysis = object()
    context.recommendation_analysis = object()
    context.confidence_analysis = object()
    engine = RecordingEngine()

    TraceabilityStage(engine).run(context)

    assert context.traceability_analysis is engine.result
    assert engine.inputs == {
        "global_analysis": context.global_analysis,
        "recommendation_analysis": context.recommendation_analysis,
        "confidence": context.confidence_analysis,
    }


def test_traceability_stage_delegates_without_building_identifiers_or_links():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.global_analysis = object()
    context.recommendation_analysis = object()
    engine = RecordingEngine()

    TraceabilityStage(engine).run(context)

    assert context.traceability_analysis is engine.result
    assert engine.inputs["confidence"] is None

