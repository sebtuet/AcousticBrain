from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.global_synthesis import GlobalSynthesisStage
from acousticbrain.models import GlobalAnalysis, Measurement, StereoAnalysis


class RecordingSynthesizer:
    def __init__(self):
        self.inputs = None
        self.result = GlobalAnalysis()

    def synthesize(self, **inputs):
        self.inputs = inputs
        return self.result


def test_global_synthesis_stage_stores_result_from_explicit_analyses():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.stereo = StereoAnalysis()
    context.peak_classification = object()
    context.confidence_analysis = object()
    synthesizer = RecordingSynthesizer()

    GlobalSynthesisStage(synthesizer).run(context)

    assert context.global_analysis is synthesizer.result
    assert synthesizer.inputs == {
        "stereo": context.stereo,
        "sbir": None,
        "modal_density": None,
        "peak_classification": context.peak_classification,
        "rt60": None,
        "etc": None,
        "clarity": None,
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


def test_global_synthesis_stage_contains_no_fallback_business_rules():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    synthesizer = RecordingSynthesizer()

    GlobalSynthesisStage(synthesizer).run(context)

    assert context.global_analysis is synthesizer.result
    assert synthesizer.inputs == {
        "stereo": None,
        "sbir": None,
        "modal_density": None,
        "peak_classification": None,
        "rt60": None,
        "etc": None,
        "clarity": None,
        "spatial": None,
        "clarity_correlations": None,
        "spatial_correlations": None,
        "etc_reflection_correlations": None,
        "direct_reverberant": None,
        "direct_reverberant_correlations": None,
        "bass_decay": None,
        "bass_decay_correlations": None,
        "confidence": None,
    }
