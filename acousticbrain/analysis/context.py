from dataclasses import dataclass, field

from acousticbrain.models import Measurement


@dataclass
class AnalysisContext:

    measurement: Measurement

    peaks: list = field(default_factory=list)

    dips: list = field(default_factory=list)

    bands: list = field(default_factory=list)

    room_modes: list = field(default_factory=list)

    mode_matches: list = field(default_factory=list)

    stereo = None

    room_properties = None

    project = None

    comparison = None