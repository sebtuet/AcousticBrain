from math import exp, log2

from acousticbrain.analysis import AnalysisContext, FrequencyResponseFeatureAnalyzer
from acousticbrain.brain.stages.frequency_response_feature import (
    FrequencyResponseFeatureStage,
)
from acousticbrain.models import (
    AnalysisReadiness,
    Measurement,
    MeasurementAnalysisFamily,
    MeasurementReadinessAnalysis,
    MeasurementReadinessStatus,
    Room,
)
from acousticbrain.project import Measurements, Project


def measurement(name):
    frequencies = [20.0 * 2.0 ** (index / 96.0) for index in range(481)]
    levels = [
        75.0
        - 8.0
        * exp(
            -0.5
            * ((log2(frequency) - log2(100.0)) / 0.04) ** 2
        )
        for frequency in frequencies
    ]
    return Measurement(
        name=name,
        frequency=frequencies,
        spl=levels,
        phase=[0.0] * len(frequencies),
    )


def project_with(*names):
    project = Project(
        name="frequency-response",
        room=Room(name="room", length=5.0, width=4.0, height=2.5),
    )
    for name in names:
        project.add_measurement(name, measurement(name))
    return project


def context():
    result = AnalysisContext(measurement=measurement(Measurements.STEREO))
    result.measurement_readiness_analysis = MeasurementReadinessAnalysis(
        analyses=(
            AnalysisReadiness(
                family=MeasurementAnalysisFamily.FREQUENCY,
                status=MeasurementReadinessStatus.AVAILABLE,
                confidence=90.0,
            ),
        ),
        confidence=90.0,
    )
    return result


def test_stage_uses_loaded_measurements_and_stores_structured_analysis():
    project = project_with(
        Measurements.LEFT,
        Measurements.RIGHT,
        Measurements.STEREO,
    )
    analysis_context = context()

    FrequencyResponseFeatureStage().run(project, analysis_context)

    analysis = analysis_context.frequency_response_feature_analysis
    assert analysis is not None
    assert tuple(item.channel.value for item in analysis.channels) == (
        "LEFT",
        "RIGHT",
        "STEREO",
    )
    assert all(item.notch_count == 1 for item in analysis.channels)
    readiness = analysis_context.measurement_readiness_analysis.analyses[0]
    assert readiness.status is MeasurementReadinessStatus.AVAILABLE
    assert readiness.required_channels == tuple(
        channel for channel, _ in FrequencyResponseFeatureStage.REQUIRED
    )


def test_stage_blocks_aggregate_analysis_when_a_required_txt_role_is_missing():
    project = project_with(Measurements.LEFT, Measurements.STEREO)
    analysis_context = context()

    FrequencyResponseFeatureStage().run(project, analysis_context)

    assert analysis_context.frequency_response_feature_analysis is None
    readiness = analysis_context.measurement_readiness_analysis.analyses[0]
    assert readiness.status is MeasurementReadinessStatus.BLOCKED
    assert readiness.missing_facts == ("FREQUENCY_RESPONSE_TXT_RIGHT",)


def test_stage_reports_invalid_grid_without_hiding_the_input_problem():
    project = project_with(
        Measurements.LEFT,
        Measurements.RIGHT,
        Measurements.STEREO,
    )
    project.get_measurement(Measurements.RIGHT).frequency[10] = float("nan")
    analysis_context = context()

    FrequencyResponseFeatureStage().run(project, analysis_context)

    assert analysis_context.frequency_response_feature_analysis is None
    readiness = analysis_context.measurement_readiness_analysis.analyses[0]
    assert readiness.status is MeasurementReadinessStatus.BLOCKED
    assert readiness.missing_facts == (
        "VALID_FREQUENCY_RESPONSE_DATA_RIGHT",
    )


def test_stage_does_not_mutate_loaded_measurements():
    project = project_with(
        Measurements.LEFT,
        Measurements.RIGHT,
        Measurements.STEREO,
    )
    before = {
        name: (
            tuple(project.get_measurement(name).frequency),
            tuple(project.get_measurement(name).spl),
            tuple(project.get_measurement(name).phase),
        )
        for name in project.list_measurements()
    }

    FrequencyResponseFeatureStage(FrequencyResponseFeatureAnalyzer()).run(
        project,
        context(),
    )

    after = {
        name: (
            tuple(project.get_measurement(name).frequency),
            tuple(project.get_measurement(name).spl),
            tuple(project.get_measurement(name).phase),
        )
        for name in project.list_measurements()
    }
    assert after == before
