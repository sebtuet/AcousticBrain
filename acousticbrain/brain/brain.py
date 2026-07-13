from .pipeline import BrainPipeline

from acousticbrain.application import AcousticSession
from acousticbrain.report import ExperimentDiscoveryPresenter, Report


class AcousticBrain:

    def __init__(self):

        self.pipeline = BrainPipeline()

    def analyze(
        self,
        project=None,
        *,
        session_context=None,
        plan_experiments=False,
        measurement_root=None,
    ):

        experiment_descriptors = ()
        if measurement_root is not None:
            if project is not None or session_context is not None:
                raise ValueError(
                    "measurement_root cannot be combined with project or session_context."
                )
            acoustic_session = AcousticSession.auto_open(measurement_root)
            project = acoustic_session.current_project
            experiment_descriptors = acoustic_session.descriptors
            plan_experiments = True
            if project is None:
                report = Report(project_name=str(measurement_root))
                context = type(
                    "DiscoveryContext",
                    (),
                    {"experiment_descriptors": experiment_descriptors},
                )()
                report.experiments_discovered = (
                    ExperimentDiscoveryPresenter().present(context)
                )
                return report
        if project is None:
            raise ValueError("A project or measurement_root is required.")

        return self.pipeline.run(
            project,
            session_context=session_context,
            plan_experiments=plan_experiments,
            experiment_descriptors=experiment_descriptors,
        )
