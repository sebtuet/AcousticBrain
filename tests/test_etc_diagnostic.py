from acousticbrain.analysis import AnalysisContext
from acousticbrain.diagnostics import ETCDiagnostic
from acousticbrain.models import (
    ETCAnalysis,
    ETCChannelAnalysis,
    ETCReflectionCorrelation,
    ETCReflectionCorrelationAnalysis,
    ImpulseChannel,
    Measurement,
    ReflectionEvent,
    ReflectionSurface,
)


def event(delay_ms, level_db=-10.0, sample_index=300, confidence=90.0):
    return ReflectionEvent(
        delay_ms=delay_ms,
        relative_level_db=level_db,
        absolute_time_s=delay_ms / 1000.0,
        sample_index=sample_index,
        acoustic_path_difference_m=delay_ms / 1000.0 * 343.0,
        confidence=confidence,
    )


def facts():
    left_event = event(5.0, sample_index=240)
    right_event = event(5.2, sample_index=250)
    unexplained = event(12.0, level_db=-15.0, sample_index=576)
    left = ETCChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        direct_sound_time_s=0.0,
        direct_sound_index=0,
        events=[left_event, unexplained],
        confidence=90.0,
    )
    right = ETCChannelAnalysis(
        channel=ImpulseChannel.RIGHT,
        direct_sound_time_s=0.0,
        direct_sound_index=0,
        events=[right_event],
        confidence=88.0,
    )
    etc = ETCAnalysis(
        channels={
            ImpulseChannel.LEFT: left,
            ImpulseChannel.RIGHT: right,
        },
        available_channels=[ImpulseChannel.LEFT, ImpulseChannel.RIGHT],
        common_events=[(left_event, right_event)],
        left_only_events=[unexplained],
        common_event_count=1,
        left_only_event_count=1,
        confidence=89.0,
    )
    correlation = ETCReflectionCorrelation(
        code="etc_reflection.left.240.front_wall",
        channel=ImpulseChannel.LEFT,
        event=left_event,
        surface=ReflectionSurface.FRONT_WALL,
        theoretical_delay_ms=4.9,
        measured_delay_ms=5.0,
        timing_error_ms=0.1,
        acoustic_path_difference_m=left_event.acoustic_path_difference_m,
        match_score=90.0,
        confidence=85.0,
        source_analyses=("ETCAnalysis", "SBIRAnalysis"),
    )
    correlations = ETCReflectionCorrelationAnalysis(
        correlations=[correlation],
        unmatched_events={ImpulseChannel.LEFT: [unexplained]},
        evaluated_event_count=2,
        matched_event_count=1,
        confidence=85.0,
    )
    return etc, correlations


def test_interprets_only_existing_etc_and_correlation_facts():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.etc_analysis, context.etc_reflection_correlation_analysis = facts()

    diagnostic = ETCDiagnostic().analyze(context)

    assert diagnostic.confidence == 89
    assert "communs : 1" in diagnostic.observations[1]
    assert any("Dominante LEFT à 5.00 ms" in item for item in diagnostic.observations)
    assert any("Surface candidate FRONT_WALL" in item for item in diagnostic.observations)
    assert any("Non expliqué LEFT à 12.00 ms" in item for item in diagnostic.observations)
    assert "sans explication" in diagnostic.conclusion
    assert len(diagnostic.recommendations) == 2


def test_does_not_reinterpret_weak_or_late_events_as_dominant():
    weak = event(25.0, level_db=-30.0)
    channel = ETCChannelAnalysis(
        channel=ImpulseChannel.STEREO,
        direct_sound_time_s=0.0,
        direct_sound_index=0,
        events=[weak],
        confidence=80.0,
    )
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.etc_analysis = ETCAnalysis(
        channels={ImpulseChannel.STEREO: channel},
        available_channels=[ImpulseChannel.STEREO],
        confidence=80.0,
    )

    diagnostic = ETCDiagnostic().analyze(context)

    assert diagnostic.severity == "LOW"
    assert diagnostic.score == 100.0
    assert "Aucune réflexion précoce dominante" in diagnostic.conclusion


def test_handles_absent_etc_analysis():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    diagnostic = ETCDiagnostic().analyze(context)

    assert diagnostic.severity == "INFO"
    assert diagnostic.confidence == 0
    assert "indisponible" in diagnostic.message

