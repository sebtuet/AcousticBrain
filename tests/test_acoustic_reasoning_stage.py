from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.acoustic_reasoning import AcousticReasoningStage
from acousticbrain.models import AcousticReasoningAnalysis, Measurement


class RecordingEngine:
    def __init__(self):
        self.inputs = None
        self.result = AcousticReasoningAnalysis((), (), 0.0)

    def analyze(self, **inputs):
        self.inputs = inputs
        return self.result


def test_stage_maps_only_structured_knowledge_layers_explicitly():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.stereo = object()
    context.spatial_analysis = object()
    context.etc_analysis = object()
    context.room_geometry = object()
    engine = RecordingEngine()

    AcousticReasoningStage(engine).run(context)

    assert context.acoustic_reasoning_analysis is engine.result
    assert engine.inputs == {
        "stereo": context.stereo,
        "spatial": context.spatial_analysis,
        "spatial_correlations": context.spatial_correlation_analysis,
        "etc": context.etc_analysis,
        "etc_reflection_correlations": context.etc_reflection_correlation_analysis,
        "direct_reverberant": context.direct_reverberant_analysis,
        "direct_reverberant_correlations": context.direct_reverberant_correlation_analysis,
        "bass_decay": context.bass_decay_analysis,
        "bass_decay_correlations": context.bass_decay_correlation_analysis,
        "modal_density": context.modal_density,
        "sbir": context.sbir,
        "room_geometry": context.room_geometry,
    }
