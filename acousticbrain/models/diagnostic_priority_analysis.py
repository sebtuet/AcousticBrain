from dataclasses import dataclass, field

from .prioritized_diagnostic import PrioritizedDiagnostic


@dataclass
class DiagnosticPriorityAnalysis:
    """Ordre de présentation dérivé de diagnostics déjà interprétés."""

    prioritized_diagnostics: list[PrioritizedDiagnostic] = field(default_factory=list)
    tie_groups: list[list[PrioritizedDiagnostic]] = field(default_factory=list)
