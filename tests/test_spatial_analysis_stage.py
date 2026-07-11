from acousticbrain.analysis import AnalysisContext, SpatialAnalyzer
from acousticbrain.brain.stages.spatial_analysis import SpatialAnalysisStage
from acousticbrain.models import (
    ImpulseChannel,
    ImpulseResponse,
    Measurement,
    Room,
    SpatialChannelPairAnalysis,
    SpatialMeasurementType,
)
from acousticbrain.project import Project


class RecordingAnalyzer:
    def __init__(self):
        self.inputs = None
        self.result = SpatialChannelPairAnalysis(
            measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
            confidence=91.0,
        )

    def analyze(self, first, second, measurement_type):
        self.inputs = (first, second, measurement_type)
        return self.result


def project_with_pair():
    project = Project(
        name="Reference",
        room=Room(name="Room", length=5.0, width=4.0, height=2.5),
    )
    left = ImpulseResponse(
        channel=ImpulseChannel.LEFT,
        sample_rate_hz=48000.0,
        samples=[1.0],
    )
    right = ImpulseResponse(
        channel=ImpulseChannel.RIGHT,
        sample_rate_hz=48000.0,
        samples=[1.0],
    )
    project.add_impulse_response(left)
    project.add_impulse_response(right)
    return project, left, right


def test_stage_delegates_the_explicit_speaker_pair_and_stores_analysis():
    project, left, right = project_with_pair()
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    analyzer = RecordingAnalyzer()

    SpatialAnalysisStage(analyzer).run(
        project,
        context,
        SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
    )

    assert analyzer.inputs == (
        left,
        right,
        SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
    )
    assert context.spatial_analysis.pair_analysis is analyzer.result
    assert context.spatial_analysis.source_measurement_type is (
        SpatialMeasurementType.SPEAKER_CHANNEL_PAIR
    )
    assert context.spatial_analysis.confidence == 91.0


def test_stage_preserves_an_explicit_absence_when_the_pair_is_incomplete():
    project, left, _ = project_with_pair()
    project.impulse_responses = {ImpulseChannel.LEFT: left}
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    analyzer = RecordingAnalyzer()

    SpatialAnalysisStage(analyzer).run(project, context)

    assert analyzer.inputs is None
    assert context.spatial_analysis.pair_analysis is None
    assert context.spatial_analysis.source_measurement_type is (
        SpatialMeasurementType.SPEAKER_CHANNEL_PAIR
    )
    assert context.spatial_analysis.confidence == 0.0


def test_spatial_analyzer_is_publicly_exported():
    assert SpatialAnalyzer.__name__ == "SpatialAnalyzer"
