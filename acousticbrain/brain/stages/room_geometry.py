from acousticbrain.analysis import RoomGeometryBuilder
from acousticbrain.models import (
    RoomGeometryComparison,
    RoomGeometryComparisonStatus,
)


class RoomGeometryStage:
    """Résout une source géométrique sans fusion ni fallback implicite."""

    def __init__(self, builder=None):
        self.builder = builder or RoomGeometryBuilder()

    def run(self, project, context):
        if project.room_description is not None:
            geometry = self.builder.from_description(project.room_description)
            comparison = self._comparison(project)
        elif project.room is not None:
            geometry = self.builder.from_legacy_room(project.room)
            comparison = RoomGeometryComparison(
                status=RoomGeometryComparisonStatus.SINGLE_SOURCE
            )
        else:
            raise ValueError(
                "Room geometry requires RoomDescription or legacy Room."
            )

        project.room_geometry = geometry
        project.room_geometry_comparison = comparison
        context.room_geometry = geometry
        context.room_geometry_comparison = comparison

    @staticmethod
    def _comparison(project):
        if project.room is None:
            return RoomGeometryComparison(
                status=RoomGeometryComparisonStatus.SINGLE_SOURCE
            )
        declared = project.room_description.dimensions
        legacy = project.room
        pairs = (
            ("length_m", declared.length_m, legacy.length),
            ("width_m", declared.width_m, legacy.width),
            ("height_m", declared.height_m, legacy.height),
        )
        differences = {
            field: abs(declared_value - legacy_value)
            for field, declared_value, legacy_value in pairs
            if declared_value != legacy_value
        }
        return RoomGeometryComparison(
            status=(
                RoomGeometryComparisonStatus.DIVERGENT
                if differences
                else RoomGeometryComparisonStatus.EQUIVALENT
            ),
            differing_fields=tuple(differences),
            absolute_differences_m=differences,
        )
