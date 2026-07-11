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
        "confidence": None,
    }

