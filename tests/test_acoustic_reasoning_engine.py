import inspect
from types import SimpleNamespace

from acousticbrain.analysis import AcousticReasoningEngine, RoomGeometryBuilder
from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayBandAnalysis,
    BassDecayCorrelation,
    BassDecayCorrelationAnalysis,
    DecayUsability,
    DirectReverberantCorrelation,
    DirectReverberantCorrelationAnalysis,
    ETCAnalysis,
    ETCReflectionCorrelation,
    ETCReflectionCorrelationAnalysis,
    GeometryCoordinate,
    HypothesisCode,
    HypothesisStatus,
    ImpulseChannel,
    ModalDensityAnalysis,
    Peak,
    ReflectionEvent,
    ReflectionSurface,
    Room,
    SBIRAnalysis,
    SBIRCandidate,
    SBIRGeometryCorrelationAnalysis,
    SpatialAnalysis,
    SpatialChannelPairAnalysis,
    SpatialCorrelation,
    SpatialCorrelationAnalysis,
    SpatialMeasurementType,
    StereoAnalysis,
)


def usable_decay(seconds, confidence=90.0):
    return BassDecayBandAnalysis(
        center_frequency_hz=40.0,
        minimum_frequency_hz=35.0,
        maximum_frequency_hz=45.0,
        start_level_db=-5.0,
        end_level_db=-25.0,
        observed_decay_range_db=20.0,
        observed_duration_seconds=seconds / 3.0,
        decay_slope_db_per_second=-60.0 / seconds,
        estimated_decay_time_seconds=seconds,
        noise_floor_db=-60.0,
        noise_margin_db=35.0,
        fit_correlation=-0.98,
        confidence=confidence,
        method="T20",
        usability=DecayUsability.USABLE,
    )


def reflection(delay=5.0, level=-10.0):
    return ReflectionEvent(delay, level, 0.01, 100, 1.0, 90.0)


def sbir_analysis(best=True):
    peak = Peak(75.0, 70.0, 0, 10.0)
    candidate = SBIRCandidate(
        surface=ReflectionSurface.FLOOR,
        measured_frequency=75.0,
        theoretical_frequency=76.0,
        distance_m=1.05,
        delay_ms=6.1,
        frequency_error_hz=1.0,
        match_score=90.0,
        peak=peak,
    )
    return SBIRAnalysis(
        candidates=[candidate] if best else [],
        best_match=candidate if best else None,
        reflection_surface=ReflectionSurface.FLOOR if best else None,
        reflection_distance_m=1.05 if best else None,
        delay_ms=6.1 if best else None,
        confidence=90.0,
        score=20.0 if best else 100.0,
    )


def test_engine_always_returns_four_ordered_hypotheses_with_missing_facts():
    result = AcousticReasoningEngine().analyze()

    assert tuple(item.code for item in result.hypotheses) == tuple(HypothesisCode)
    assert all(item.status is HypothesisStatus.INCONCLUSIVE for item in result.hypotheses)
    assert all(item.support_score == 0.0 for item in result.hypotheses)
    assert all(item.missing_facts for item in result.hypotheses)
    assert all(not item.verification_actions for item in result.hypotheses)


def test_sbir_analysis_states_distinguish_not_evaluated_from_no_admissible_match():
    room_geometry = RoomGeometryBuilder().from_legacy_room(
        Room("Room", 5.84, 5.5, 2.6)
    )

    not_evaluated = AcousticReasoningEngine().analyze(
        room_geometry=room_geometry,
    ).hypotheses[3]
    no_match_analysis = SBIRGeometryCorrelationAnalysis(
        correlations=(),
        best_match=None,
        unmatched_candidate_ids=("geometry_sbir.front_wall",),
        evaluated_candidate_count=1,
        observed_dip_count=1,
        confidence=0.0,
        source_analysis_codes=(
            "GeometrySBIRAnalysis",
            "PeakDetectionAnalysis",
        ),
        applied_rule_codes=("SBIR_DETERMINISTIC_BEST_MATCH_V1",),
    )
    no_admissible_match = AcousticReasoningEngine().analyze(
        sbir_geometry_correlations=no_match_analysis,
        room_geometry=room_geometry,
    ).hypotheses[3]

    assert {
        item.fact_code for item in not_evaluated.missing_facts
    } >= {"sbir.best_match"}
    assert "sbir.best_match" not in {
        item.fact_code for item in no_admissible_match.missing_facts
    }
    status = next(
        item
        for item in no_admissible_match.context_evidence
        if item.fact_code == "sbir.geometry_correlation_status"
    )
    assert status.value == "NO_ADMISSIBLE_MATCH"
    assert status.role.name == "CONTEXT"
    assert no_admissible_match.supporting_evidence == ()
    assert no_admissible_match.counter_evidence == ()
    assert "SBIR_GEOMETRY_NO_ADMISSIBLE_MATCH" in (
        no_admissible_match.applied_rule_codes
    )


def test_sbir_geometry_match_found_remains_positive_non_causal_evidence():
    candidate = SimpleNamespace(
        surface_id="front_wall",
        base_surface_id="front_wall",
        speaker_id="LEFT",
        listening_position_id="LISTENING_POSITION",
        relationship_code="FRONT_WALL",
        candidate_id="geometry_sbir.front_wall",
        geometry_path_id="geometry_reflection.front_wall",
        speaker_boundary_distance_m=0.54,
        extra_distance_m=1.0,
        expected_cancellation_frequency_hz=85.75,
        frequency_uncertainty_hz=None,
        confidence=88.0,
    )
    match = SimpleNamespace(
        code="sbir_geometry.left.front_wall.1",
        candidate=candidate,
        observed_dip=Peak(86.0, 50.0, 1, 12.0),
        frequency_error_hz=0.25,
        frequency_error_percent=0.29,
        match_score=98.0,
        confidence=93.0,
    )
    result = AcousticReasoningEngine().analyze(
        sbir_geometry_correlations=SimpleNamespace(best_match=match),
        room_geometry=RoomGeometryBuilder().from_legacy_room(
            Room("Room", 5.84, 5.5, 2.6)
        ),
    ).hypotheses[3]

    assert any(
        item.fact_code == "sbir.geometry_frequency_match"
        for item in result.supporting_evidence
    )
    assert "SBIR_GEOMETRY_COMPATIBILITY_NON_CAUSAL" in (
        result.applied_rule_codes
    )
    assert not any(
        item.fact_code == "sbir.geometry_correlation_status"
        for item in result.context_evidence
    )


def test_asymmetry_rule_combines_independent_structured_evidence():
    stereo = StereoAnalysis(
        left_only_peaks=[Peak(60.0, 80.0, 0, 10.0)],
        right_only_peaks=[Peak(70.0, 80.0, 0, 8.0)],
    )
    pair = SpatialChannelPairAnalysis(
        measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        broadband_level_difference_db=3.0,
        confidence=80.0,
    )
    spatial = SpatialAnalysis(
        pair_analysis=pair,
        source_measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        confidence=80.0,
    )
    correlations = SpatialCorrelationAnalysis(
        correlations=(
            SpatialCorrelation(
                code="SPATIAL_LEVEL_STEREO_IMBALANCE",
                score=90.0,
                confidence=80.0,
            ),
        )
    )
    etc = ETCAnalysis(
        left_only_event_count=8,
        right_only_event_count=1,
        confidence=90.0,
    )

    result = AcousticReasoningEngine().analyze(
        stereo=stereo,
        spatial=spatial,
        spatial_correlations=correlations,
        etc=etc,
    )
    hypothesis = result.hypotheses[0]

    assert hypothesis.status is HypothesisStatus.SUPPORTED
    assert hypothesis.support_score >= 70.0
    assert hypothesis.confidence != hypothesis.support_score
    assert len(hypothesis.supporting_evidence) == 3
    assert hypothesis.context_evidence
    assert hypothesis.counter_evidence == ()
    assert hypothesis.verification_actions[0].code == "VERIFY_SPEAKER_ROOM_ASYMMETRY"


def test_modal_rule_distinguishes_support_from_short_decay_counter_evidence():
    supported = AcousticReasoningEngine().analyze(
        bass_decay=BassDecayAnalysis(
            aggregate_bands=[usable_decay(3.0)],
            confidence=90.0,
        ),
        bass_decay_correlations=BassDecayCorrelationAnalysis(
            correlations=[
                BassDecayCorrelation(
                    code="SLOW_DECAY_MODAL_INTERACTION",
                    score=90.0,
                    confidence=80.0,
                )
            ],
            confidence=80.0,
        ),
        modal_density=ModalDensityAnalysis(confidence=75.0),
    ).hypotheses[1]
    contradicted = AcousticReasoningEngine().analyze(
        bass_decay=BassDecayAnalysis(
            aggregate_bands=[usable_decay(0.6)],
            confidence=90.0,
        ),
        bass_decay_correlations=BassDecayCorrelationAnalysis(
            confidence=90.0,
        ),
    ).hypotheses[1]

    assert supported.status is HypothesisStatus.SUPPORTED
    assert supported.supporting_evidence
    assert supported.verification_actions[0].code == "VERIFY_MODAL_BASS_PERSISTENCE"
    assert contradicted.status is HypothesisStatus.CONTRADICTED
    assert contradicted.counter_evidence[0].fact_code == "bass_decay.maximum_decay_time"
    assert contradicted.verification_actions == ()


def test_early_reflection_rule_requires_dominant_structured_events():
    etc = ETCAnalysis(available_channels=[ImpulseChannel.LEFT], confidence=90.0)
    correlations = ETCReflectionCorrelationAnalysis(
        unmatched_events={ImpulseChannel.LEFT: [reflection() for _ in range(10)]},
        evaluated_event_count=10,
        confidence=85.0,
    )
    drr = DirectReverberantCorrelationAnalysis(
        correlations=[
            DirectReverberantCorrelation(
                code="LOW_DRR_DOMINANT_EARLY_REFLECTIONS",
                score=90.0,
                confidence=80.0,
            )
        ]
    )

    hypothesis = AcousticReasoningEngine().analyze(
        etc=etc,
        etc_reflection_correlations=correlations,
        direct_reverberant_correlations=drr,
    ).hypotheses[2]

    assert hypothesis.status is HypothesisStatus.SUPPORTED
    assert {item.fact_code for item in hypothesis.supporting_evidence} == {
        "etc_reflection.dominant_unmatched_event_count",
        "direct_reverberant.correlation.LOW_DRR_DOMINANT_EARLY_REFLECTIONS",
    }
    assert hypothesis.verification_actions[0].definitive is False


def test_early_reflection_action_names_the_testable_geometry_surface():
    observed = reflection(delay=3.0)
    correlation = ETCReflectionCorrelation(
        code="etc_geometry_reflection.left.100.left_side_wall_panel_02",
        channel=ImpulseChannel.LEFT,
        event=observed,
        surface=ReflectionSurface.LEFT_WALL,
        theoretical_delay_ms=2.86,
        measured_delay_ms=3.0,
        timing_error_ms=0.14,
        acoustic_path_difference_m=observed.acoustic_path_difference_m,
        match_score=88.0,
        confidence=86.0,
        source_analyses=("ETCAnalysis", "GeometryEarlyReflectionAnalysis"),
        surface_id="LEFT_SIDE_WALL_PANEL_02",
        impact_point=GeometryCoordinate(2.0, 0.0, 1.0),
        geometric_uncertainty_ms=0.2,
        geometry_confidence=88.0,
        geometry_path_id=(
            "geometry_reflection.LEFT.MIC.LEFT_SIDE_WALL_PANEL_02"
        ),
        provenance_codes=("LASER_MEASURED",),
    )
    correlations = ETCReflectionCorrelationAnalysis(
        correlations=[correlation],
        unmatched_events={ImpulseChannel.LEFT: []},
        evaluated_event_count=1,
        matched_event_count=1,
        confidence=86.0,
    )

    hypothesis = AcousticReasoningEngine().analyze(
        etc=ETCAnalysis(
            available_channels=[ImpulseChannel.LEFT], confidence=90.0
        ),
        etc_reflection_correlations=correlations,
    ).hypotheses[2]

    action = hypothesis.verification_actions[0]
    assert action.parameters["surface"] == "LEFT_SIDE_WALL_PANEL_02"
    assert action.parameters["observed_event_delay_ms"] == 3.0
    assert action.parameters["observed_event_relative_level_db"] == -10.0
    assert action.parameters["theoretical_delay_ms"] == 2.86
    assert action.parameters["timing_error_ms"] == 0.14
    assert action.parameters["geometry_confidence"] == 88.0
    assert action.expected_supporting_fact_codes == (
        "REFLECTION_DECREASES_AFTER_MASKING",
    )
    assert action.expected_counter_fact_codes == (
        "REFLECTION_REMAINS_UNCHANGED_AFTER_MASKING",
    )


def test_sbir_rule_keeps_geometry_and_frequency_context_and_verification_parameters():
    geometry = RoomGeometryBuilder().from_legacy_room(Room("Room", 5.0, 4.0, 2.5))

    hypothesis = AcousticReasoningEngine().analyze(
        sbir=sbir_analysis(),
        room_geometry=geometry,
    ).hypotheses[3]

    assert hypothesis.status is HypothesisStatus.SUPPORTED
    assert {item.fact_code for item in hypothesis.context_evidence} == {
        "sbir.reflection_surface",
        "sbir.measured_frequency_hz",
        "room_geometry.source",
    }
    action = hypothesis.verification_actions[0]
    assert action.code == "VERIFY_SBIR_PLACEMENT"
    assert action.parameters["surface"] == "FLOOR"
    assert action.parameters["current_distance_m"] == 1.05


def test_engine_has_no_raw_signal_or_diagnostic_dependency():
    source = inspect.getsource(AcousticReasoningEngine)

    assert "ImpulseResponse" not in source
    assert ".samples" not in source
    assert "Diagnostic" not in source
