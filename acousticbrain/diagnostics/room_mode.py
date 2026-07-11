from acousticbrain.models import EvidenceLevel, RoomModeType

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

            message=self._message(best),

            causes=[
                "Correspondance avec le calcul théorique"
            ],

            recommendations=[
                "Vérifier le placement du point d'écoute",
                "Ne pas corriger immédiatement avec un EQ",
            ],

        )

    @staticmethod
    def _message(match):
        mode = match.mode
        mode_label = {
            RoomModeType.AXIAL: "axial",
            RoomModeType.TANGENTIAL: "tangentiel",
            RoomModeType.OBLIQUE: "oblique",
        }[mode.mode_type]
        modal_order = (
            f"ordre {mode.order}"
            if mode.mode_type is RoomModeType.AXIAL
            else f"indices ({mode.order_x}, {mode.order_y}, {mode.order_z})"
        )
        return (
            f"Mode {mode_label} {mode.axis} "
            f"({modal_order}) à {match.peak.frequency:.2f} Hz"
        )
