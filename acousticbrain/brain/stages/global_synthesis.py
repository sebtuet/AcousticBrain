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
            rt60=context.rt60_analysis,
            etc=context.etc_analysis,
            clarity=context.clarity_analysis,
            spatial=context.spatial_analysis,
            clarity_correlations=context.clarity_correlation_analysis,
            spatial_correlations=context.spatial_correlation_analysis,
            etc_reflection_correlations=(
                context.etc_reflection_correlation_analysis
            ),
            direct_reverberant=context.direct_reverberant_analysis,
            direct_reverberant_correlations=(
                context.direct_reverberant_correlation_analysis
            ),
            bass_decay=context.bass_decay_analysis,
            bass_decay_correlations=context.bass_decay_correlation_analysis,
            confidence=getattr(context, "confidence_analysis", None),
        )
