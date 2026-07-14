from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.geometry_sbir import GeometrySBIRStage
from acousticbrain.models import Measurement


class RecordingEngine:
    def __init__(self):
        self.inputs = None
        self.result = object()

    def analyze(self, reflections, geometry):
        self.inputs = (reflections, geometry)
        return self.result


def test_geometry_sbir_stage_only_delegates_derived_geometry():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.geometry_early_reflection_analysis = object()
    context.room_geometry = object()
    engine = RecordingEngine()

    GeometrySBIRStage(engine).run(context)

    assert engine.inputs == (
        context.geometry_early_reflection_analysis,
        context.room_geometry,
    )
    assert context.geometry_sbir_analysis is engine.result
