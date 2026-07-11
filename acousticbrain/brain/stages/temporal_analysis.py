from acousticbrain.analysis import RT60Aggregator, RT60Analyzer


class TemporalAnalysisStage:
    """Orchestre les analyses temporelles déjà importées dans le projet."""

    def __init__(self, analyzer=None, aggregator=None):
        self.analyzer = analyzer or RT60Analyzer()
        self.aggregator = aggregator or RT60Aggregator()

    def run(self, project, context):
        channel_analyses = {
            channel: self.analyzer.analyze(impulse_response)
            for channel, impulse_response in project.impulse_responses.items()
        }
        context.rt60_analysis = self.aggregator.aggregate(channel_analyses)

