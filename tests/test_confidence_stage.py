from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.confidence import ConfidenceStage
from acousticbrain.models import Measurement


class RecordingEngine:
    def __init__(self):
        self.input = None
        self.result = object()

    def analyze(self, analyses):
        self.input = analyses
        return self.result


def test_stage_maps_all_physical_analyses_explicitly():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.modal_density = object()
    context.sbir = object()
    context.stereo = object()
    context.rt60_analysis = object()
    context.etc_analysis = object()
    context.clarity_analysis = object()
    context.spatial_analysis = object()
    engine = RecordingEngine()

    ConfidenceStage(engine).run(context)

    assert engine.input == {
        "modal_density": context.modal_density,
        "sbir": context.sbir,
        "stereo": context.stereo,
        "rt60": context.rt60_analysis,
        "etc": context.etc_analysis,
        "clarity": context.clarity_analysis,
        "spatial": context.spatial_analysis,
    }
    assert context.confidence_analysis is engine.result
