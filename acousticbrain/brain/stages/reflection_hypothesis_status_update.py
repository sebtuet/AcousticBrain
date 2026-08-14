from acousticbrain.models import ControlledReflectionHypothesisStatusUpdate


class ControlledReflectionHypothesisStatusUpdateStage:
    """Publishes persisted observation statuses without affecting reasoning."""

    def run(self, project, context):
        updates = tuple(project.controlled_reflection_hypothesis_status_updates)
        if any(
            not isinstance(item, ControlledReflectionHypothesisStatusUpdate)
            for item in updates
        ):
            raise ValueError("Project hypothesis status updates must be typed.")
        context.controlled_reflection_hypothesis_status_updates = tuple(sorted(
            updates,
            key=lambda item: item.update_id,
        ))
