from dataclasses import fields

import pytest

from acousticbrain.analysis import ETCReflectionCorrelationEngine
from acousticbrain.models import (
    ETCAnalysis,
    ETCChannelAnalysis,
    ETCReflectionCorrelation,
    ETCReflectionCorrelationAnalysis,
    GeometryCoordinate,
    GeometryEarlyReflectionAnalysis,
    GeometryReflectionPath,
    ImpulseChannel,
    Peak,
    ReflectionEvent,
    ReflectionSurface,
    SBIRAnalysis,
    SBIRCandidate,
)


def event(delay_ms, sample_index=300, confidence=80.0):
    return ReflectionEvent(
        delay_ms=delay_ms,
        relative_level_db=-12.0,
        absolute_time_s=delay_ms / 1000.0,
        sample_index=sample_index,
        acoustic_path_difference_m=delay_ms / 1000.0 * 343.0,
        confidence=confidence,
    )


def candidate(surface, delay_ms, match_score=90.0):
    return SBIRCandidate(
        surface=surface,
        measured_frequency=80.0,
        theoretical_frequency=82.0,
        distance_m=delay_ms / 1000.0 * 343.0 / 2.0,
        delay_ms=delay_ms,
        frequency_error_hz=2.0,
        match_score=match_score,
        peak=Peak(
            frequency=80.0,
            spl=70.0,
            index=0,
            prominence=8.0,
        ),
    )


def inputs():
    matched = event(6.2, sample_index=300)
    unmatched = event(10.0, sample_index=480)
    channel = ETCChannelAnalysis(
        channel=ImpulseChannel.LEFT,
        direct_sound_time_s=0.0,
        direct_sound_index=0,
        events=[matched, unmatched],
        confidence=88.0,
    )
    etc = ETCAnalysis(
        channels={ImpulseChannel.LEFT: channel},
        available_channels=[ImpulseChannel.LEFT],
        confidence=88.0,
    )
    front = candidate(ReflectionSurface.FRONT_WALL, 6.0)
    sbir = SBIRAnalysis(
        candidates=[front],
        best_match=front,
        reflection_surface=front.surface,
        reflection_distance_m=front.distance_m,
        delay_ms=front.delay_ms,
        confidence=85.0,
        score=15.0,
    )
    return etc, sbir, matched, unmatched


def test_correlates_existing_facts_with_deterministic_provenance():
    etc, sbir, matched, unmatched = inputs()

    result = ETCReflectionCorrelationEngine().analyze(etc, sbir)

    assert result.evaluated_event_count == 2
    assert result.matched_event_count == 1
    assert result.available_surfaces == (ReflectionSurface.FRONT_WALL,)
    assert result.unmatched_events == {ImpulseChannel.LEFT: [unmatched]}

    correlation = result.correlations[0]
    assert correlation.code == "etc_reflection.left.300.front_wall"
    assert correlation.event is matched
    assert correlation.surface is ReflectionSurface.FRONT_WALL
    assert correlation.theoretical_delay_ms == 6.0
    assert correlation.measured_delay_ms == 6.2
    assert correlation.timing_error_ms == pytest.approx(0.2)
    assert correlation.acoustic_path_difference_m == matched.acoustic_path_difference_m
    assert correlation.match_score == pytest.approx(83.0)
    assert correlation.confidence == pytest.approx(82.4)
    assert correlation.source_analyses == ("ETCAnalysis", "SBIRAnalysis")


def test_keeps_events_unmatched_outside_the_explicit_timing_threshold():
    etc, sbir, matched, unmatched = inputs()

    result = ETCReflectionCorrelationEngine().analyze(
        etc,
        sbir,
        maximum_timing_error_ms=0.1,
    )

    assert result.correlations == []
    assert result.unmatched_events[ImpulseChannel.LEFT] == [matched, unmatched]
    assert result.confidence == 0.0


def test_filters_surfaces_and_weak_sbir_candidates_explicitly():
    etc, sbir, matched, unmatched = inputs()
    weak = candidate(ReflectionSurface.FLOOR, 6.2, match_score=40.0)
    sbir.candidates.append(weak)

    result = ETCReflectionCorrelationEngine().analyze(
        etc,
        sbir,
        surfaces=(ReflectionSurface.FLOOR,),
    )

    assert result.available_surfaces == ()
    assert result.correlations == []
    assert result.unmatched_events[ImpulseChannel.LEFT] == [matched, unmatched]


def test_returns_explicit_absence_without_sbir_candidates():
    etc, _, matched, unmatched = inputs()
    sbir = SBIRAnalysis([], None, None, None, None, 0.0, 100.0)

    result = ETCReflectionCorrelationEngine().analyze(etc, sbir)

    assert result.correlations == []
    assert result.available_surfaces == ()
    assert result.unmatched_events[ImpulseChannel.LEFT] == [matched, unmatched]


def test_returns_explicit_absence_without_sbir_analysis():
    etc, _, matched, unmatched = inputs()

    result = ETCReflectionCorrelationEngine().analyze(etc, None)

    assert result.correlations == []
    assert result.unmatched_events[ImpulseChannel.LEFT] == [matched, unmatched]


def test_correlates_exact_named_geometry_surface_with_observed_event():
    observed = event(3.0, sample_index=144, confidence=90.0)
    etc = ETCAnalysis(
        channels={
            ImpulseChannel.LEFT: ETCChannelAnalysis(
                channel=ImpulseChannel.LEFT,
                direct_sound_time_s=0.0,
                direct_sound_index=0,
                events=[observed],
                confidence=90.0,
            )
        },
        available_channels=[ImpulseChannel.LEFT],
        confidence=90.0,
    )
    path = GeometryReflectionPath(
        path_id="geometry_reflection.LEFT.MIC.LEFT_SIDE_WALL_PANEL_02",
        speaker_id="LEFT",
        listening_position_id="MIC",
        surface_id="LEFT_SIDE_WALL_PANEL_02",
        base_surface_id="left_wall",
        surface=ReflectionSurface.LEFT_WALL,
        impact_point=GeometryCoordinate(2.0, 0.0, 1.0),
        direct_path_m=2.0,
        reflected_path_m=2.98,
        acoustic_path_difference_m=0.98,
        theoretical_delay_ms=2.86,
        uncertainty_ms=0.2,
        confidence=88.0,
        provenance_codes=("LASER_MEASURED",),
    )
    geometry = GeometryEarlyReflectionAnalysis(
        paths=(path,),
        source_analysis_codes=("RoomGeometry",),
        applied_rule_codes=("GEOMETRY_IMAGE_SOURCE_FIRST_ORDER",),
    )

    result = ETCReflectionCorrelationEngine().analyze(
        etc, None, geometry_reflections=geometry
    )

    correlation = result.correlations[0]
    assert correlation.surface_id == "LEFT_SIDE_WALL_PANEL_02"
    assert correlation.geometry_path_id == path.path_id
    assert correlation.measured_delay_ms == 3.0
    assert correlation.theoretical_delay_ms == 2.86
    assert correlation.timing_error_ms == pytest.approx(0.14)
    assert correlation.geometric_uncertainty_ms == 0.2
    assert correlation.geometry_confidence == 88.0
    assert correlation.impact_point == path.impact_point
    assert correlation.provenance_codes == ("LASER_MEASURED",)
    assert result.available_surface_ids == ("LEFT_SIDE_WALL_PANEL_02",)
    assert result.geometry_candidate_count == 1


def test_correlation_contract_contains_no_user_text_or_action():
    field_names = {
        field.name
        for model in (
            ETCReflectionCorrelation,
            ETCReflectionCorrelationAnalysis,
        )
        for field in fields(model)
    }

    assert field_names.isdisjoint(
        {
            "diagnostic",
            "message",
            "recommendation",
            "recommendations",
            "severity",
            "title",
        }
    )
