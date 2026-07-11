from dataclasses import dataclass, field

from acousticbrain.diagnostics import Diagnostic

from .traceability_presenter import PresentedTraceabilityAnalysis


@dataclass
class Report:

    project_name: str

    room_properties = None

    diagnostics: list[Diagnostic] = field(default_factory=list)

    traceability_analysis: PresentedTraceabilityAnalysis | None = None

    def add(self, diagnostic):

        self.diagnostics.append(diagnostic)
