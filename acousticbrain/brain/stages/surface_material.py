from acousticbrain.analysis import SurfaceMaterialAnalyzer


class SurfaceMaterialStage:
    """Stage factuel immédiatement postérieur à la géométrie de propagation."""

    def __init__(self, analyzer=None):
        self.analyzer = analyzer or SurfaceMaterialAnalyzer()

    def run(self, project, context):
        analysis = self.analyzer.analyze(
            project.room_description,
            context.propagation_geometry,
        )
        project.surface_material_analysis = analysis
        context.surface_material_analysis = analysis
