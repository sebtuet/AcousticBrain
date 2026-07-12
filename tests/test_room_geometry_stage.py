import pytest

from acousticbrain.analysis import AnalysisContext, RoomGeometryBuildException
from acousticbrain.brain.stages.room_geometry import RoomGeometryStage
from acousticbrain.models import (
    GeometrySource,
    Measurement,
    Room,
    RoomDescription,
    RoomDimensions,
    RoomGeometry,
    RoomGeometryModel,
    RoomGeometryComparison,
    RoomGeometryComparisonStatus,
    RoomSurface,
)
from acousticbrain.project import Project


def geometry(source):
    return RoomGeometry(
        dimensions=RoomDimensions(5.0, 4.0, 2.5),
        surfaces=(),
        source=source,
        model=RoomGeometryModel.RECTANGULAR,
        completeness=60.0,
    )


class RecordingBuilder:
    def __init__(self):
        self.calls = []
        self.description_result = geometry(GeometrySource.ROOM_DESCRIPTION)
        self.legacy_result = geometry(GeometrySource.LEGACY_ROOM)

    def from_description(self, description):
        self.calls.append(("description", description))
        return self.description_result

    def from_legacy_room(self, room):
        self.calls.append(("legacy", room))
        return self.legacy_result


def context():
    return AnalysisContext(measurement=Measurement(name="L+R"))


def description():
    return RoomDescription(
        name="Declared",
        dimensions=RoomDimensions(6.0, 5.0, 2.7),
    )


def test_description_is_the_explicit_source_when_both_sources_exist():
    declared = description()
    legacy = Room("Legacy", 5.0, 4.0, 2.5)
    project = Project("Project", legacy, room_description=declared)
    analysis_context = context()
    builder = RecordingBuilder()

    RoomGeometryStage(builder).run(project, analysis_context)

    assert builder.calls == [("description", declared)]
    assert project.room_geometry is builder.description_result
    assert analysis_context.room_geometry is builder.description_result
    assert project.room_geometry.source is GeometrySource.ROOM_DESCRIPTION
    assert project.room_geometry_comparison.status is (
        RoomGeometryComparisonStatus.DIVERGENT
    )
    assert project.room_geometry_comparison.differing_fields == (
        "length_m",
        "width_m",
        "height_m",
    )


def test_legacy_is_used_only_when_description_is_absent():
    legacy = Room("Legacy", 5.0, 4.0, 2.5)
    project = Project("Project", legacy)
    analysis_context = context()
    builder = RecordingBuilder()

    RoomGeometryStage(builder).run(project, analysis_context)

    assert builder.calls == [("legacy", legacy)]
    assert project.room_geometry.source is GeometrySource.LEGACY_ROOM
    assert analysis_context.room_geometry is project.room_geometry
    assert project.room_geometry_comparison.status is (
        RoomGeometryComparisonStatus.SINGLE_SOURCE
    )


def test_description_failure_never_falls_back_to_legacy_or_mutates_targets():
    declared = description()
    project = Project(
        "Project",
        Room("Legacy", 5.0, 4.0, 2.5),
        room_description=declared,
    )
    analysis_context = context()
    previous = geometry(GeometrySource.LEGACY_ROOM)
    project.room_geometry = previous
    analysis_context.room_geometry = previous
    previous_comparison = RoomGeometryComparison(
        status=RoomGeometryComparisonStatus.SINGLE_SOURCE
    )
    project.room_geometry_comparison = previous_comparison
    analysis_context.room_geometry_comparison = previous_comparison

    class FailingBuilder(RecordingBuilder):
        def from_description(self, description):
            self.calls.append(("description", description))
            raise RoomGeometryBuildException(("INVALID",))

    builder = FailingBuilder()

    with pytest.raises(RoomGeometryBuildException):
        RoomGeometryStage(builder).run(project, analysis_context)

    assert builder.calls == [("description", declared)]
    assert project.room_geometry is previous
    assert analysis_context.room_geometry is previous
    assert project.room_geometry_comparison is previous_comparison
    assert analysis_context.room_geometry_comparison is previous_comparison


def test_total_absence_of_geometry_is_rejected_explicitly():
    project = Project("Project", None)
    analysis_context = context()

    with pytest.raises(ValueError, match="RoomDescription or legacy Room"):
        RoomGeometryStage().run(project, analysis_context)

    assert project.room_geometry is None
    assert analysis_context.room_geometry is None


def test_equivalent_sources_are_reported_without_divergence():
    legacy = Room("Legacy", 6.0, 5.0, 2.7)
    project = Project(
        "Project",
        legacy,
        room_description=description(),
    )
    analysis_context = context()

    RoomGeometryStage().run(project, analysis_context)

    comparison = project.room_geometry_comparison
    assert comparison.status is RoomGeometryComparisonStatus.EQUIVALENT
    assert comparison.differing_fields == ()
    assert dict(comparison.absolute_differences_m) == {}


def test_project_and_context_geometry_are_optional_before_stage_execution():
    project = Project("Project", Room("Legacy", 5.0, 4.0, 2.5))
    analysis_context = context()

    assert project.room_geometry is None
    assert analysis_context.room_geometry is None
