from acousticbrain.analysis import ReflectionCandidateCompatibilityEngine


class MaterialAwareReflectionCandidateStage:
    """Publishes a leaf analysis from three already-built source analyses."""

    def __init__(self, engine=None):
        self.engine = engine or ReflectionCandidateCompatibilityEngine()

    def run(self, context):
        context.material_aware_reflection_candidate_analysis = self.engine.analyze(
            context.geometry_early_reflection_analysis,
            context.etc_reflection_correlation_analysis,
            context.surface_material_analysis,
        )
