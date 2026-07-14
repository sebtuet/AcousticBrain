from acousticbrain.analysis import AcousticReasoningEngine


class AcousticReasoningStage:
    """Orchestre le raisonnement après les analyses et corrélations."""

    def __init__(self, engine=None):
        self.engine = engine or AcousticReasoningEngine()

    def run(self, context):
        context.acoustic_reasoning_analysis = self.engine.analyze(
            stereo=context.stereo,
            spatial=context.spatial_analysis,
            spatial_correlations=context.spatial_correlation_analysis,
            etc=context.etc_analysis,
            etc_reflection_correlations=(
                context.etc_reflection_correlation_analysis
            ),
            direct_reverberant=context.direct_reverberant_analysis,
            direct_reverberant_correlations=(
                context.direct_reverberant_correlation_analysis
            ),
            bass_decay=context.bass_decay_analysis,
            bass_decay_correlations=context.bass_decay_correlation_analysis,
            modal_density=context.modal_density,
            sbir=context.sbir,
            sbir_geometry_correlations=(
                context.sbir_geometry_correlation_analysis
            ),
            room_geometry=context.room_geometry,
        )
