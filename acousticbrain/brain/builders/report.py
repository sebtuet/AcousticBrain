from acousticbrain.report import (
    GlobalPresenter,
    RecommendationPresenter,
    Report,
    TraceabilityPresenter,
    RoomGeometryPresenter,
    OptimizationSessionPresenter,
    ExperimentPlanningPresenter,
    ExperimentDiscoveryPresenter,
)


class ReportBuilder:
    """
    Construit le rapport d'analyse.
    """

    def build(self, project, context):

        report = Report(
            project_name=project.name
        )

        report.room_properties = (
            context.room_properties
        )

        report.recommendations = RecommendationPresenter().present(context)
        report.global_analysis = GlobalPresenter().present(context)
        report.traceability_analysis = TraceabilityPresenter().present(context)
        report.room_geometry = RoomGeometryPresenter().present(context)
        report.optimization_session = OptimizationSessionPresenter().present(context)
        report.experiment_planning = ExperimentPlanningPresenter().present(context)
        report.experiments_discovered = ExperimentDiscoveryPresenter().present(context)

        return report
