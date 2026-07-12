from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.bass_decay_correlation import (
    BassDecayCorrelationStage,
)
from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayCorrelationAnalysis,
    DirectReverberantAnalysis,
    Measurement,
    ModalDensityAnalysis,
    RoomModesAnalysis,
    RT60Analysis,
)


class RecordingEngine:
    def __init__(self):
        self.inputs = None
        self.result = BassDecayCorrelationAnalysis()

    def correlate(self, *inputs):
        self.inputs = inputs
        return self.result


def test_stage_only_delegates_structured_analyses():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.bass_decay_analysis = BassDecayAnalysis()
    context.room_modes_analysis = RoomModesAnalysis(
        [], [], [], [], 0.0, 0.0, 0, 0, 0, 0, 0.0
    )
    context.modal_density = ModalDensityAnalysis()
    context.rt60_analysis = RT60Analysis()
    context.direct_reverberant_analysis = DirectReverberantAnalysis()
    engine = RecordingEngine()

    BassDecayCorrelationStage(engine).run(context)

    assert engine.inputs == (
        context.bass_decay_analysis,
        context.room_modes_analysis,
        context.modal_density,
        context.rt60_analysis,
        context.direct_reverberant_analysis,
    )
    assert context.bass_decay_correlation_analysis is engine.result
