from acousticbrain.report import RecommendationPresenter, Report


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

        return report
