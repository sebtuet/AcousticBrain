from acousticbrain.analysis import TraceabilityEngine


class TraceabilityStage:
    """Orchestre la traçabilité lorsque ses connaissances sont disponibles."""

    def __init__(self, engine=None):
        self.engine = engine or TraceabilityEngine()

    def run(self, context):
        context.traceability_analysis = self.engine.analyze(
            global_analysis=context.global_analysis,
            recommendation_analysis=context.recommendation_analysis,
            rt60=context.rt60_analysis,
            etc=context.etc_analysis,
            clarity=context.clarity_analysis,
            spatial=context.spatial_analysis,
            spatial_interpretation=context.spatial_interpretation,
            clarity_correlations=context.clarity_correlation_analysis,
            spatial_correlations=context.spatial_correlation_analysis,
            etc_reflection_correlations=(
                context.etc_reflection_correlation_analysis
            ),
            direct_reverberant=context.direct_reverberant_analysis,
            direct_reverberant_correlations=(
                context.direct_reverberant_correlation_analysis
            ),
            bass_decay=context.bass_decay_analysis,
            bass_decay_correlations=context.bass_decay_correlation_analysis,
            confidence=getattr(context, "confidence_analysis", None),
            measurement_quality=context.measurement_quality_analysis,
            measurement_readiness=context.measurement_readiness_analysis,
            room_geometry=context.room_geometry,
            room_geometry_comparison=context.room_geometry_comparison,
            propagation_geometry=context.propagation_geometry,
            acoustic_reasoning=context.acoustic_reasoning_analysis,
            experiment_planning=context.experiment_planning_analysis,
            material_aware_reflection_candidates=(
                context.material_aware_reflection_candidate_analysis
            ),
            controlled_reflection_verification_planning=(
                context.controlled_reflection_verification_planning_analysis
            ),
            controlled_reflection_experiment_declarations=(
                context.controlled_reflection_experiment_declarations
            ),
        )
