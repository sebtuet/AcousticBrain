from acousticbrain.analysis import ConfidenceEngine


class ConfidenceStage:
    """Transmet explicitement les confiances locales déjà disponibles."""

    def __init__(self, engine=None):
        self.engine = engine or ConfidenceEngine()

    def run(self, context):
        context.confidence_analysis = self.engine.analyze(
            {
                "modal_density": context.modal_density,
                "sbir": context.sbir,
                "stereo": context.stereo,
                "rt60": context.rt60_analysis,
                "etc": context.etc_analysis,
                "clarity": context.clarity_analysis,
                "spatial": context.spatial_analysis,
                "direct_reverberant": context.direct_reverberant_analysis,
                "bass_decay": context.bass_decay_analysis,
                "measurement_quality": context.measurement_quality_analysis,
                "measurement_readiness": context.measurement_readiness_analysis,
            }
        )
