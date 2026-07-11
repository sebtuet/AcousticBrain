from dataclasses import dataclass, field

from acousticbrain.diagnostics import Diagnostic
from acousticbrain.models import DiagnosticPriorityAnalysis


@dataclass
class Report:

    project_name: str

    room_properties = None

    diagnostics: list[Diagnostic] = field(default_factory=list)

    diagnostic_priority: DiagnosticPriorityAnalysis | None = None

    def add(self, diagnostic):

        self.diagnostics.append(diagnostic)
