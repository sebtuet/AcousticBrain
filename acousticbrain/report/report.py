from dataclasses import dataclass, field

from acousticbrain.diagnostics import Diagnostic

from .global_presenter import PresentedGlobalAnalysis


@dataclass
class Report:

    project_name: str

    room_properties = None

    diagnostics: list[Diagnostic] = field(default_factory=list)

    global_analysis: PresentedGlobalAnalysis | None = None

    def add(self, diagnostic):

        self.diagnostics.append(diagnostic)
