from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.temporal_analysis import TemporalAnalysisStage
from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayChannelAnalysis,
    ClarityAnalysis,
    ClarityChannelAnalysis,
    DirectReverberantAnalysis,
    DirectReverberantChannelAnalysis,
    ETCAnalysis,
    ETCChannelAnalysis,
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


class RecordingETCAnalyzer(RecordingAnalyzer):
    def analyze(self, impulse_response):
        self.inputs.append(impulse_response)
        return ETCChannelAnalysis(
            channel=impulse_response.channel,
            direct_sound_time_s=0.0,
            direct_sound_index=0,
        )


class RecordingETCAggregator(RecordingAggregator):
    def __init__(self):
        self.input = None
        self.result = ETCAnalysis()


class RecordingClarityAnalyzer(RecordingAnalyzer):
    def analyze(self, impulse_response):
        self.inputs.append(impulse_response)
        return ClarityChannelAnalysis(channel=impulse_response.channel)


class RecordingClarityAggregator(RecordingAggregator):
    def __init__(self):
        self.input = None
        self.result = ClarityAnalysis()


class RecordingDirectReverberantAnalyzer(RecordingAnalyzer):
    def analyze(self, impulse_response):
        self.inputs.append(impulse_response)
        return DirectReverberantChannelAnalysis(
            channel=impulse_response.channel
        )


class RecordingDirectReverberantAggregator(RecordingAggregator):
    def __init__(self):
        self.input = None
        self.result = DirectReverberantAnalysis()


class RecordingBassDecayAnalyzer(RecordingAnalyzer):
    def analyze(self, impulse_response):
        self.inputs.append(impulse_response)
        return BassDecayChannelAnalysis(channel=impulse_response.channel)


class RecordingBassDecayAggregator(RecordingAggregator):
    def __init__(self):
        self.input = None
        self.result = BassDecayAnalysis()


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
    etc_analyzer = RecordingETCAnalyzer()
    etc_aggregator = RecordingETCAggregator()
    clarity_analyzer = RecordingClarityAnalyzer()
    clarity_aggregator = RecordingClarityAggregator()
    direct_reverberant_analyzer = RecordingDirectReverberantAnalyzer()
    direct_reverberant_aggregator = RecordingDirectReverberantAggregator()
    bass_decay_analyzer = RecordingBassDecayAnalyzer()
    bass_decay_aggregator = RecordingBassDecayAggregator()

    TemporalAnalysisStage(
        analyzer,
        aggregator,
        etc_analyzer,
        etc_aggregator,
        clarity_analyzer,
        clarity_aggregator,
        direct_reverberant_analyzer,
        direct_reverberant_aggregator,
        bass_decay_analyzer,
        bass_decay_aggregator,
    ).run(project, context)

    assert analyzer.inputs == [left, stereo]
    assert set(aggregator.input) == {
        ImpulseChannel.LEFT,
        ImpulseChannel.STEREO,
    }
    assert context.rt60_analysis is aggregator.result
    assert etc_analyzer.inputs == [left, stereo]
    assert set(etc_aggregator.input) == {
        ImpulseChannel.LEFT,
        ImpulseChannel.STEREO,
    }
    assert context.etc_analysis is etc_aggregator.result
    assert clarity_analyzer.inputs == [left, stereo]
    assert set(clarity_aggregator.input) == {
        ImpulseChannel.LEFT,
        ImpulseChannel.STEREO,
    }
    assert context.clarity_analysis is clarity_aggregator.result
    assert direct_reverberant_analyzer.inputs == [left, stereo]
    assert set(direct_reverberant_aggregator.input) == {
        ImpulseChannel.LEFT,
        ImpulseChannel.STEREO,
    }
    assert (
        context.direct_reverberant_analysis
        is direct_reverberant_aggregator.result
    )
    assert bass_decay_analyzer.inputs == [left, stereo]
    assert set(bass_decay_aggregator.input) == {
        ImpulseChannel.LEFT,
        ImpulseChannel.STEREO,
    }
    assert context.bass_decay_analysis is bass_decay_aggregator.result


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
