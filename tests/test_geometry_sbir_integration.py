from types import SimpleNamespace

from acousticbrain.analysis import (
    AcousticReasoningEngine,
    ExperimentPlanner,
    GeometryEarlyReflectionEngine,
    GeometrySBIRPredictionEngine,
    RecommendationEngine,
    RoomGeometryBuilder,
    SBIRGeometryCorrelationEngine,
)
from acousticbrain.diagnostics import SBIRDiagnostic
from acousticbrain.models import (
    GeometryDatumQualityDescription,
    HypothesisCode,
    HypothesisStatus,
    ListeningPosition,
    Peak,
    RoomDescription,
    RoomDimensions,
    SpeakerOrientation,
    SpeakerPosition,
)


def test_geometry_sbir_chain_remains_structured_auditable_and_non_causal():
    quality_ids = (
        "LEFT", "MIC", "front_wall", "rear_wall",
        "left_wall", "right_wall", "floor", "ceiling",
    )
    description = RoomDescription(
        "SBIR integration",
        RoomDimensions(5.0, 4.0, 3.0),
        speakers=(SpeakerPosition(
            "LEFT", 1.0, 1.0, 1.0, SpeakerOrientation(0.0)
        ),),
        listening_positions=(ListeningPosition("MIC", 3.0, 1.0, 1.0),),
        geometry_data_quality=tuple(
            GeometryDatumQualityDescription(
                item, 0.01, 88.0, ("LASER_MEASURED",)
            )
            for item in quality_ids
        ),
    )
    room = RoomGeometryBuilder().from_description(description)
    paths = GeometryEarlyReflectionEngine().analyze(room)
    predictions = GeometrySBIRPredictionEngine().analyze(paths, room)
    correlations = SBIRGeometryCorrelationEngine().analyze(
        predictions, (Peak(86.0, 50.0, 1, 12.0),)
    )

    reasoning = AcousticReasoningEngine().analyze(
        sbir_geometry_correlations=correlations,
        room_geometry=room,
    )
    hypothesis = next(
        item for item in reasoning.hypotheses
        if item.code is HypothesisCode.SBIR_PLACEMENT_INTERACTION
    )
    action = hypothesis.verification_actions[0]

    assert "SBIR_GEOMETRY_COMPATIBILITY_NON_CAUSAL" in (
        hypothesis.applied_rule_codes
    )
    assert hypothesis.status is HypothesisStatus.PLAUSIBLE
    assert {
        item.fact_code for item in hypothesis.missing_facts
    } >= {"verification.sbir_response_to_speaker_move"}
    assert action.parameters["surface"] == "front_wall"
    assert action.parameters["speaker_id"] == "LEFT"
    assert action.parameters["predicted_frequency_hz"] == 85.75
    assert action.parameters["measured_frequency_hz"] == 86.0
    assert action.parameters["geometry_confidence"] == 88.0
    assert action.expected_supporting_fact_codes == (
        "SBIR_MOVES_WITH_SPEAKER",
    )
    assert action.expected_counter_fact_codes == ("SBIR_REMAINS_FIXED",)
    assert action.definitive is False

    recommendation = next(
        item for item in RecommendationEngine().analyze(
            acoustic_reasoning=reasoning
        ).recommendations
        if item.code == "VERIFY_SBIR_PLACEMENT"
    )
    assert recommendation.verification_action is True
    assert recommendation.parameters["geometry_candidate_id"]
    assert recommendation.parameters["frequency_uncertainty_percent"] == 3.0
    assert recommendation.source_analyses == (
        "SBIRGeometryCorrelationAnalysis",
    )

    planning = ExperimentPlanner().plan(reasoning)
    candidate = next(
        item for item in planning.plan.ordered_candidates
        if item.hypothesis_code == "SBIR_PLACEMENT_INTERACTION"
    )
    assert candidate.source_protocol_id == "protocol.temporary_move_speaker.v1"
    assert candidate.changed_variable_codes == ("LOUDSPEAKER_POSITION",)
    assert "MICROPHONE_POSITION" in candidate.controlled_variable_codes
    assert "SBIR_MOVES_WITH_SPEAKER" in candidate.observable_fact_codes
    assert "SBIR_REMAINS_FIXED" in candidate.observable_fact_codes

    diagnostic = SBIRDiagnostic().analyze(SimpleNamespace(
        sbir=None,
        sbir_geometry_correlation_analysis=correlations,
    ))
    assert diagnostic.title == "SBIR géométrique"
    assert "sans attribution causale" in diagnostic.conclusion
    assert diagnostic.recommendations == []
