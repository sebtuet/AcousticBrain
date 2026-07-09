from acousticbrain.models import EvidenceLevel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class RoomModeDiagnostic(DiagnosticBase):

    def analyze(self, context):

        if len(context.mode_matches) == 0:

            return Diagnostic(

                title="Modes propres",

                severity="OK",

                confidence=100,

                evidence_level=EvidenceLevel.CALCULATED,

                message="Aucun mode identifié."

            )

        best = max(
            context.mode_matches,
            key=lambda match: match.confidence
        )

        return Diagnostic(

            title="Modes propres",

            severity="HIGH",

            confidence=int(best.confidence),

            evidence_level=EvidenceLevel.CONFIRMED,

            message=(
                f"Mode axial {best.mode.axis} "
                f"(ordre {best.mode.order}) "
                f"à {best.peak.frequency:.2f} Hz"
            ),

            causes=[
                "Correspondance avec le calcul théorique"
            ],

            recommendations=[
                "Vérifier le placement du point d'écoute",
                "Ne pas corriger immédiatement avec un EQ",
            ],

        )