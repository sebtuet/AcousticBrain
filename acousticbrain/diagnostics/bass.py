from acousticbrain.models import EvidenceLevel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class BassDiagnostic(DiagnosticBase):

    def analyze(self, context):

        bass_band = context.bands[0]

        if len(bass_band.peaks) == 0:

            return Diagnostic(

                title="Réponse dans le grave",

                severity="OK",

                confidence=100,

                evidence_level=EvidenceLevel.OBSERVED,

                message="Aucun pic détecté."

            )

        strongest = max(
            bass_band.peaks,
            key=lambda peak: peak.prominence
        )

        severity = "LOW"

        if strongest.prominence > 15:
            severity = "HIGH"

        elif strongest.prominence > 8:
            severity = "MEDIUM"

        return Diagnostic(

            title="Réponse dans le grave",

            severity=severity,

            confidence=95,

            evidence_level=EvidenceLevel.OBSERVED,

            message=(
                f"Pic dominant à "
                f"{strongest.frequency:.1f} Hz "
                f"(prominence {strongest.prominence:.1f} dB)"
            ),

            causes=[
                "Mode propre de la pièce",
                "Position d'écoute",
                "Interaction enceinte / mur",
            ],

            recommendations=[
                "Mesurer chaque enceinte séparément",
                "Vérifier la position d'écoute",
            ],

        )