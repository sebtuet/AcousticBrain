from acousticbrain.report import (
    GlobalPresenter,
    RecommendationPresenter,
    Report,
    TraceabilityPresenter,
    RoomGeometryPresenter,
    OptimizationSessionPresenter,
    ExperimentPlanningPresenter,
    ExperimentDiscoveryPresenter,
    ExperimentComparisonPresenter,
    CausalDiscriminationPresenter,
    ExperimentCampaignPresenter,
    SurfaceMaterialPresenter,
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
        report.experiment_comparison = ExperimentComparisonPresenter().present(context)
        report.experiment_campaigns = ExperimentCampaignPresenter().present(context)
        report.causal_discrimination = CausalDiscriminationPresenter().present(context)
        report.surface_materials = SurfaceMaterialPresenter().present(context)

        return report
