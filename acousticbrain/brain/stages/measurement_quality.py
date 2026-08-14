from acousticbrain.analysis import (
    MeasurementQualityAggregator,
    MeasurementQualityAnalyzer,
    MeasurementSetQualityAnalyzer,
)


class MeasurementQualityStage:
    """Orchestre les faits de qualité avant les analyses acoustiques."""

    def __init__(
        self,
        channel_analyzer=None,
        set_analyzer=None,
        aggregator=None,
    ):
        self.channel_analyzer = channel_analyzer or MeasurementQualityAnalyzer()
        self.set_analyzer = set_analyzer or MeasurementSetQualityAnalyzer()
        self.aggregator = aggregator or MeasurementQualityAggregator()

    def run(self, project, context):
        channel_qualities = {
            channel: self.channel_analyzer.analyze(impulse_response)
            for channel, impulse_response in project.impulse_responses.items()
        }
        set_quality = self.set_analyzer.analyze(channel_qualities)
        context.measurement_quality_analysis = self.aggregator.aggregate(
            channel_qualities,
            set_quality,
        )
