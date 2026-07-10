from dataclasses import dataclass, field

from acousticbrain.models import (
    Measurement,
    RoomProperties,
    StereoAnalysis,
)

from acousticbrain.project import Project


@dataclass
class AnalysisContext:

    measurement: Measurement

    peaks: list = field(default_factory=list)

    dips: list = field(default_factory=list)

    bands: list = field(default_factory=list)

    room_modes: list = field(default_factory=list)

    mode_matches: list = field(default_factory=list)

    stereo: StereoAnalysis | None = None

    room_properties: RoomProperties | None = None

    project: Project | None = None

    comparison = None