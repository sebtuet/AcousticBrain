from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.temporal_analysis import TemporalAnalysisStage
from acousticbrain.models import (
    ImpulseChannel,
    ImpulseResponse,
    Measurement,
    RT60Analysis,
    RT60ChannelAnalysis,
    Room,
)
from acousticbrain.project import Project


class RecordingAnalyzer:
    def __init__(self):
        self.inputs = []

    def analyze(self, impulse_response):
        self.inputs.append(impulse_response)
        return RT60ChannelAnalysis(channel=impulse_response.channel)


class RecordingAggregator:
    def __init__(self):
        self.input = None
        self.result = RT60Analysis()

    def aggregate(self, channel_analyses):
        self.input = channel_analyses
        return self.result


def test_temporal_stage_analyzes_each_imported_channel_and_stores_aggregation():
    project = Project(
        name="Reference",
        room=Room(name="Room", length=5.0, width=4.0, height=2.5),
    )
    left = ImpulseResponse(
        channel=ImpulseChannel.LEFT,
        sample_rate_hz=48_000,
        samples=[1.0],
    )
    stereo = ImpulseResponse(
        channel=ImpulseChannel.STEREO,
        sample_rate_hz=48_000,
        samples=[1.0],
    )
    project.add_impulse_response(left)
    project.add_impulse_response(stereo)
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    analyzer = RecordingAnalyzer()
    aggregator = RecordingAggregator()

    TemporalAnalysisStage(analyzer, aggregator).run(project, context)

    assert analyzer.inputs == [left, stereo]
    assert set(aggregator.input) == {
        ImpulseChannel.LEFT,
        ImpulseChannel.STEREO,
    }
    assert context.rt60_analysis is aggregator.result


def test_project_stores_impulses_by_explicit_channel():
    project = Project(
        name="Reference",
        room=Room(name="Room", length=5.0, width=4.0, height=2.5),
    )
    impulse = ImpulseResponse(
        channel=ImpulseChannel.RIGHT,
        sample_rate_hz=48_000,
        samples=[1.0],
    )

    project.add_impulse_response(impulse)

    assert project.get_impulse_response(ImpulseChannel.RIGHT) is impulse

