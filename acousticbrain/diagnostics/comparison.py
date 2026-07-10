from acousticbrain.models import EvidenceLevel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class ComparisonDiagnostic(DiagnosticBase):

    def analyze(self, context):

        if context.comparison is None:

            return Diagnostic(

                title="Comparaison",

                severity="INFO",

                confidence=100,

                evidence_level=EvidenceLevel.OBSERVED,

                message="Une seule mesure disponible."

            )

        biggest = max(

            context.comparison,

            key=lambda x: abs(x.difference)

        )

        return Diagnostic(

            title="Comparaison des mesures",

            severity="INFO",

            confidence=100,

            evidence_level=EvidenceLevel.OBSERVED,

            message=(

                f"Ecart maximal "

                f"{abs(biggest.difference):.1f} dB "

                f"à {biggest.frequency:.1f} Hz"

            ),

            recommendations=[

                "Comparer les deux mesures",

                "Identifier l'origine de l'écart",

            ],

        )