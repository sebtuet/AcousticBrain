from acousticbrain.analysis import BassDecayCorrelationEngine


class BassDecayCorrelationStage:
    """Orchestre uniquement le croisement d'analyses déjà produites."""

    def __init__(self, engine=None):
        self.engine = engine or BassDecayCorrelationEngine()

    def run(self, context):
        context.bass_decay_correlation_analysis = self.engine.correlate(
            context.bass_decay_analysis,
            context.room_modes_analysis,
            context.modal_density,
            context.rt60_analysis,
            context.direct_reverberant_analysis,
        )
