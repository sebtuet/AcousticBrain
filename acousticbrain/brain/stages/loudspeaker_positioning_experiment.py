from acousticbrain.analysis import LoudspeakerPositioningExperimentEngine
from acousticbrain.project import Measurements


class LoudspeakerPositioningExperimentStage:
    """Projette une expérience sans modifier ses analyses sources."""

    def __init__(self, engine=None):
        self.engine = engine or LoudspeakerPositioningExperimentEngine()

    def run(self, context):
        project = context.project
        context.loudspeaker_positioning_experiment_analysis = self.engine.analyze(
            experiment_planning=context.experiment_planning_analysis,
            recommendation_analysis=context.recommendation_analysis,
            room_geometry=context.room_geometry,
            measurements_available=(
                project is not None
                and all(project.has_measurement(name) for name in (
                    Measurements.LEFT,
                    Measurements.RIGHT,
                    Measurements.STEREO,
                ))
            ),
        )
