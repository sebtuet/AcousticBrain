from dataclasses import dataclass, field

from acousticbrain.diagnostics import Diagnostic
from acousticbrain.models import DiagnosticPriorityAnalysis

from .recommendation import PresentedRecommendation

from .global_presenter import PresentedGlobalAnalysis

from .traceability_presenter import PresentedTraceabilityAnalysis
from .room_geometry_presenter import PresentedRoomGeometry


@dataclass
class Report:

    project_name: str

    room_properties = None

    diagnostics: list[Diagnostic] = field(default_factory=list)

    diagnostic_priority: DiagnosticPriorityAnalysis | None = None

    recommendations: list[PresentedRecommendation] = field(default_factory=list)

    global_analysis: PresentedGlobalAnalysis | None = None

    traceability_analysis: PresentedTraceabilityAnalysis | None = None

    room_geometry: PresentedRoomGeometry | None = None

    def add(self, diagnostic):

        self.diagnostics.append(diagnostic)
