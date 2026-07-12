from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.recommendation import RecommendationStage
from acousticbrain.models import Measurement, RecommendationAnalysis, StereoAnalysis


class RecordingEngine:
    def __init__(self):
        self.inputs = None

    def analyze(self, **inputs):
        self.inputs = inputs
        return RecommendationAnalysis()


def test_recommendation_stage_stores_the_engine_result_from_explicit_analyses():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.stereo = StereoAnalysis()
    context.confidence_analysis = object()
    engine = RecordingEngine()

    RecommendationStage(engine).run(context)

    assert isinstance(context.recommendation_analysis, RecommendationAnalysis)
    assert engine.inputs == {
        "stereo": context.stereo,
        "sbir": None,
        "modal_density": None,
        "peak_classification": None,
        "rt60": None,
        "etc": None,
        "spatial": None,
        "clarity_correlations": None,
        "spatial_correlations": None,
        "etc_reflection_correlations": None,
        "direct_reverberant": None,
        "direct_reverberant_correlations": None,
        "bass_decay": None,
        "bass_decay_correlations": None,
        "confidence": context.confidence_analysis,
    }
