from acousticbrain.models import ControlledReflectionExperimentComparison


class ControlledReflectionExperimentComparisonStage:
    """Publishes persisted comparisons without recalculating or interpreting them."""

    def run(self, project, context):
        comparisons = tuple(project.controlled_reflection_experiment_comparisons)
        if any(
            not isinstance(item, ControlledReflectionExperimentComparison)
            for item in comparisons
        ):
            raise ValueError("Project reflection comparisons must be typed.")
        context.controlled_reflection_experiment_comparisons = tuple(sorted(
            comparisons,
            key=lambda item: item.comparison_id,
        ))
