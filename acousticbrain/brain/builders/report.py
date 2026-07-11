from acousticbrain.report import Report, TraceabilityPresenter


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

        report.traceability_analysis = TraceabilityPresenter().present(context)

        return report
