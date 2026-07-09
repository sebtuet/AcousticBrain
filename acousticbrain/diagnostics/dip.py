from acousticbrain.models import EvidenceLevel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class DipDiagnostic(DiagnosticBase):

    def analyze(self, context):

        if len(context.dips) == 0:

            return Diagnostic(

                title="Creux importants",

                severity="OK",

                confidence=100,

                evidence_level=EvidenceLevel.OBSERVED,

                message="Aucun creux important détecté."

            )

        deepest = max(
            context.dips,
            key=lambda dip: dip.prominence
        )

        severity = "LOW"

        if deepest.prominence > 15:
            severity = "HIGH"

        elif deepest.prominence > 8:
            severity = "MEDIUM"

        return Diagnostic(

            title="Creux importants",

            severity=severity,

            confidence=90,

            evidence_level=EvidenceLevel.OBSERVED,

            message=(
                f"Creux principal à "
                f"{deepest.frequency:.1f} Hz "
                f"(prominence {deepest.prominence:.1f} dB)"
            ),

            recommendations=[
                "Identifier l'origine du creux",
                "Comparer les mesures gauche / droite",
                "Mesurer le subwoofer séparément",
            ],

        )