from acousticbrain.analysis import SpatialAnalyzer
from acousticbrain.models import (
    ImpulseChannel,
    SpatialAnalysis,
    SpatialMeasurementType,
)


class SpatialAnalysisStage:
    """Orchestre l'analyse technique d'une paire d'impulsions existantes."""

    def __init__(self, analyzer=None):
        self.analyzer = analyzer or SpatialAnalyzer()

    def run(
        self,
        project,
        context,
        measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
    ):
        left = project.get_impulse_response(ImpulseChannel.LEFT)
        right = project.get_impulse_response(ImpulseChannel.RIGHT)
        if left is None or right is None:
            context.spatial_analysis = SpatialAnalysis(
                source_measurement_type=measurement_type,
            )
            return

        pair_analysis = self.analyzer.analyze(
            left,
            right,
            measurement_type,
        )
        context.spatial_analysis = SpatialAnalysis(
            pair_analysis=pair_analysis,
            source_measurement_type=measurement_type,
            confidence=pair_analysis.confidence,
        )
