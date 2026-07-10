class DiagnosticsStage:
    """
    Exécute tous les diagnostics
    et les ajoute au rapport.
    """

    def __init__(self, diagnostics):

        self.diagnostics = diagnostics

    def run(self, context, report):

        for diagnostic in self.diagnostics:

            report.add(
                diagnostic.analyze(
                    context
                )
            )
            