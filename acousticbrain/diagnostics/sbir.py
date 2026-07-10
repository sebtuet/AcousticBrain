from acousticbrain.models import EvidenceLevel

from acousticbrain.physics import SBIRCalculator

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class SBIRDiagnostic(DiagnosticBase):

    def analyze(self, context):

        speaker = context.project.get_speaker("Left")

        if speaker is None:

            return Diagnostic(

                title="SBIR",

                severity="OK",

                confidence=100,

                evidence_level=EvidenceLevel.CALCULATED,

                message="Aucune enceinte définie."

            )

        modes = SBIRCalculator().calculate(
            speaker
        )

        lines = []

        for mode in modes:

            lines.append(

                f"{mode.surface}: "

                f"{mode.frequency:.1f} Hz"

            )

        return Diagnostic(

            title="SBIR",

            severity="INFO",

            confidence=100,

            evidence_level=EvidenceLevel.CALCULATED,

            message="\n".join(lines),

            recommendations=[

                "Comparer ces fréquences aux creux mesurés",

            ],

        )