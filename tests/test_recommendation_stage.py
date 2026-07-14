from types import SimpleNamespace

from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.recommendation import RecommendationStage
from acousticbrain.models import (
    CausalDiscriminationDecision,
    CausalDiscriminationDecisionReason,
    CausalDiscriminationDecisionStatus,
    Measurement,
    Recommendation,
    RecommendationAnalysis,
    RecommendationPriority,
    RecommendationStatus,
    StereoAnalysis,
)


class RecordingEngine:
    def __init__(self):
        self.inputs = None

    def analyze(self, **inputs):
        self.inputs = inputs
        return RecommendationAnalysis()


class VerificationEngine:
    def analyze(self, **inputs):
        return RecommendationAnalysis([Recommendation(
            code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
            action="compare",
            target="left_right_measurements_and_placement",
            priority=RecommendationPriority.HIGH,
            confidence=70.0,
            source_analyses=("AcousticReasoningAnalysis",),
            verification_action=True,
        )])


class MultiPositionEngine:
    def analyze(self, **inputs):
        return RecommendationAnalysis([Recommendation(
            code="MEASURE_MULTIPLE_POSITIONS",
            action="measure",
            target="listening_area",
            priority=RecommendationPriority.HIGH,
            confidence=75.0,
            source_analyses=("ModalDensityAnalysis",),
        )])


def test_recommendation_stage_stores_the_engine_result_from_explicit_analyses():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.stereo = StereoAnalysis()
    context.confidence_analysis = object()
    engine = RecordingEngine()

    RecommendationStage(engine).run(context)

    assert isinstance(context.recommendation_analysis, RecommendationAnalysis)
    assert engine.inputs == {
        "stereo": context.stereo,
        "sbir": None,
        "modal_density": None,
        "peak_classification": None,
        "rt60": None,
        "etc": None,
        "spatial": None,
        "clarity_correlations": None,
        "spatial_correlations": None,
        "etc_reflection_correlations": None,
        "direct_reverberant": None,
        "direct_reverberant_correlations": None,
        "bass_decay": None,
        "bass_decay_correlations": None,
        "confidence": context.confidence_analysis,
        "measurement_quality": context.measurement_quality_analysis,
            "measurement_readiness": context.measurement_readiness_analysis,
            "acoustic_reasoning": context.acoustic_reasoning_analysis,
        }


def test_stage_marks_user_deferred_verification_without_removing_traceability():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    decision = CausalDiscriminationDecision(
        protocol_code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
        discrimination_code="LOUDSPEAKER_VS_ROOM_SIDE",
        status=CausalDiscriminationDecisionStatus.DEFERRED,
        reason=CausalDiscriminationDecisionReason.USER_DECISION,
        experiment_id="exp-002",
    )
    context.experiment_descriptors = (
        SimpleNamespace(causal_discrimination_decisions=(decision,)),
    )

    RecommendationStage(VerificationEngine()).run(context)

    recommendation = context.recommendation_analysis.recommendations[0]
    assert recommendation.code == "VERIFY_SPEAKER_ROOM_ASYMMETRY"
    assert recommendation.status is RecommendationStatus.DEFERRED
    assert recommendation.status_reason == "USER_DECISION"


def test_stage_marks_completed_physical_protocol_recommendation():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.experiment_descriptors = (SimpleNamespace(
        source_protocol_id="protocol.verify_modal_bass_persistence.v1",
        declared_change_codes=("MULTIPLE_LISTENING_POSITIONS",),
        causal_discrimination_decisions=(),
    ),)

    RecommendationStage(MultiPositionEngine()).run(context)

    recommendation = context.recommendation_analysis.recommendations[0]
    assert recommendation.status is RecommendationStatus.COMPLETED
    assert recommendation.status_reason == "EXPERIMENT_PROTOCOL_COMPLETED"
