from acousticbrain.analysis import (
    ClarityAggregator,
    ClarityAnalyzer,
    ETCAggregator,
    ETCAnalyzer,
    RT60Aggregator,
    RT60Analyzer,
)


class TemporalAnalysisStage:
    """Orchestre les analyses temporelles déjà importées dans le projet."""

    def __init__(
        self,
        analyzer=None,
        aggregator=None,
        etc_analyzer=None,
        etc_aggregator=None,
        clarity_analyzer=None,
        clarity_aggregator=None,
    ):
        self.analyzer = analyzer or RT60Analyzer()
        self.aggregator = aggregator or RT60Aggregator()
        self.etc_analyzer = etc_analyzer or ETCAnalyzer()
        self.etc_aggregator = etc_aggregator or ETCAggregator()
        self.clarity_analyzer = clarity_analyzer or ClarityAnalyzer()
        self.clarity_aggregator = clarity_aggregator or ClarityAggregator()

    def run(self, project, context):
        channel_analyses = {
            channel: self.analyzer.analyze(impulse_response)
            for channel, impulse_response in project.impulse_responses.items()
        }
        context.rt60_analysis = self.aggregator.aggregate(channel_analyses)
        etc_channel_analyses = {
            channel: self.etc_analyzer.analyze(impulse_response)
            for channel, impulse_response in project.impulse_responses.items()
        }
        context.etc_analysis = self.etc_aggregator.aggregate(
            etc_channel_analyses
        )
        clarity_channel_analyses = {
            channel: self.clarity_analyzer.analyze(impulse_response)
            for channel, impulse_response in project.impulse_responses.items()
        }
        context.clarity_analysis = self.clarity_aggregator.aggregate(
            clarity_channel_analyses
        )
