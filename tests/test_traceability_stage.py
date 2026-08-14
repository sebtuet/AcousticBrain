from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.traceability import TraceabilityStage
from acousticbrain.models import Measurement, TraceabilityAnalysis


class RecordingEngine:
    def __init__(self):
        self.inputs = None
        self.result = TraceabilityAnalysis()

    def analyze(self, **inputs):
        self.inputs = inputs
        return self.result


def test_traceability_stage_stores_result_from_explicit_knowledge_layers():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.global_analysis = object()
    context.recommendation_analysis = object()
    context.confidence_analysis = object()
    engine = RecordingEngine()

    TraceabilityStage(engine).run(context)

    assert context.traceability_analysis is engine.result
    assert engine.inputs == {
        "global_analysis": context.global_analysis,
        "recommendation_analysis": context.recommendation_analysis,
        "rt60": None,
        "etc": None,
        "clarity": None,
        "spatial": None,
        "spatial_interpretation": None,
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
            "room_geometry": context.room_geometry,
            "room_geometry_comparison": context.room_geometry_comparison,
            "propagation_geometry": context.propagation_geometry,
            "acoustic_reasoning": context.acoustic_reasoning_analysis,
            "experiment_planning": context.experiment_planning_analysis,
            "material_aware_reflection_candidates": (
                context.material_aware_reflection_candidate_analysis
            ),
            "controlled_reflection_verification_planning": (
                context.controlled_reflection_verification_planning_analysis
            ),
            "controlled_reflection_experiment_declarations": (
                context.controlled_reflection_experiment_declarations
            ),
            "controlled_reflection_experiment_comparisons": (
                context.controlled_reflection_experiment_comparisons
            ),
            "controlled_reflection_hypothesis_status_updates": (
                context.controlled_reflection_hypothesis_status_updates
            ),
        }


def test_traceability_stage_delegates_without_building_identifiers_or_links():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.global_analysis = object()
    context.recommendation_analysis = object()
    engine = RecordingEngine()

    TraceabilityStage(engine).run(context)

    assert context.traceability_analysis is engine.result
    assert engine.inputs["confidence"] is None
