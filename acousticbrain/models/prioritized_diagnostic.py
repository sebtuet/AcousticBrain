from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from acousticbrain.diagnostics.diagnostic import Diagnostic


@dataclass
class PrioritizedDiagnostic:
    """Référence non mutante à un diagnostic et à sa priorité de présentation."""

    diagnostic: "Diagnostic"
    priority_score: float
    rank: int
    justification: str
    is_secondary: bool
