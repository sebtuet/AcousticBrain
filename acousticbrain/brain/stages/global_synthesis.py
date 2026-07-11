from acousticbrain.analysis import GlobalSynthesizer


class GlobalSynthesisStage:
    """Orchestre la synthèse une fois les analyses physiques disponibles."""

    def __init__(self, synthesizer=None):
        self.synthesizer = synthesizer or GlobalSynthesizer()

    def run(self, context):
        context.global_analysis = self.synthesizer.synthesize(
            stereo=context.stereo,
            sbir=context.sbir,
            modal_density=context.modal_density,
            peak_classification=getattr(context, "peak_classification", None),
            confidence=getattr(context, "confidence_analysis", None),
        )
