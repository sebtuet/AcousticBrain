from acousticbrain.analysis import AnalysisContext


class ContextBuilder:
    """
    Construit le contexte d'analyse utilisé
    pendant tout le pipeline.
    """

    def build(self, project, measurement):

        context = AnalysisContext(
            measurement=measurement
        )

        context.project = project

        return context