from acousticbrain.analysis import AnalysisContext
from acousticbrain.brain.stages.physics import PhysicsStage
from acousticbrain.models import Measurement, Room, RoomModeType
from acousticbrain.project import Project


def test_physics_stage_stores_complete_modes_and_preserves_legacy_axial_view():
    project = Project(
        name="Reference",
        room=Room(name="Room", length=5.4, width=4.1, height=2.45),
    )
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    PhysicsStage().run(project, context)

    analysis = context.room_modes_analysis
    assert analysis is not None
    assert analysis.tangential_count > 0
    assert analysis.oblique_count > 0
    assert context.room_modes is analysis.axial_modes
    assert all(
        mode.mode_type is RoomModeType.AXIAL
        for mode in context.room_modes
    )

