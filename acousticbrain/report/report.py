from dataclasses import dataclass, field

from acousticbrain.diagnostics import Diagnostic


@dataclass
class Report:

    project_name: str

    diagnostics: list[Diagnostic] = field(default_factory=list)

    def add(self, diagnostic):

        self.diagnostics.append(diagnostic)
        