from acousticbrain.analysis import (
    PlanarPropagationEngine,
    RectangularPropagationEngine,
)


class PropagationGeometryStage:
    """Choisit une implémentation sans fusion ni fallback implicite."""

    def __init__(self, rectangular_engine=None, planar_engine=None):
        self.rectangular_engine = rectangular_engine or RectangularPropagationEngine()
        self.planar_engine = planar_engine or PlanarPropagationEngine()

    def run(self, project, context):
        description = project.room_description
        engine = (
            self.planar_engine
            if description is not None and description.planar_surfaces
            else self.rectangular_engine
        )
        analysis = engine.analyze(context.room_geometry, description)
        geometry = analysis.geometry
        project.propagation_geometry = geometry
        context.propagation_geometry = geometry
        context.propagation_geometry_analysis = analysis
