from acousticbrain.models import EvidenceLevel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class ModalDensityDiagnostic(DiagnosticBase):
    def analyze(self, context):
        analysis = context.modal_density

        if analysis is None or analysis.total_mode_count == 0:
            return Diagnostic(
                title="Densité modale",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.CALCULATED,
                message="Aucun mode exploitable sous la fréquence de Schroeder.",
            )

        observations = [
            (
                f"{analysis.total_mode_count} modes sont présents sous la "
                "fréquence de Schroeder."
            ),
            (
                "Répartition : "
                f"{analysis.axial_mode_count} axiaux, "
                f"{analysis.tangential_mode_count} tangentiels, "
                f"{analysis.oblique_mode_count} obliques."
            ),
            self._spacing_observation(analysis),
            "Cette analyse couvre les trois familles modales.",
        ]
        observations.extend(
            self._band_observation(band, "concentration")
            for band in analysis.dense_bands
        )
        observations.extend(
            self._band_observation(band, "zone clairsemée")
            for band in analysis.sparse_bands
        )

        severity = self._severity(analysis.score)
        conclusion = self._conclusion(analysis.score, analysis.dense_bands, analysis.sparse_bands)

        return Diagnostic(
            title="Densité modale",
            severity=severity,
            score=analysis.score,
            confidence=round(analysis.confidence),
            evidence_level=EvidenceLevel.CALCULATED,
            message=conclusion,
            observations=observations,
            conclusion=conclusion,
            causes=[
                "Dimensions de la pièce",
                "Répartition des modes propres sous la fréquence de Schroeder",
            ],
            recommendations=[
                "Interpréter les pics et creux dans les zones modales identifiées",
                "Mesurer plusieurs positions d'écoute dans le grave",
                "Vérifier la répartition des anomalies par famille modale",
            ],
        )

    @staticmethod
    def _spacing_observation(analysis):
        if analysis.average_spacing_hz is None:
            return (
                "Un seul mode est disponible : l'espacement modal ne peut "
                "pas encore être calculé."
            )

        return (
            f"Espacement modal moyen : {analysis.average_spacing_hz:.1f} Hz "
            f"(de {analysis.minimum_spacing_hz:.1f} à "
            f"{analysis.maximum_spacing_hz:.1f} Hz)."
        )

    @staticmethod
    def _band_observation(band, kind):
        spacing = (
            f", espacement moyen {band.average_spacing_hz:.1f} Hz"
            if band.average_spacing_hz is not None
            else ""
        )
        return (
            f"Entre {band.minimum_hz:.0f} et {band.maximum_hz:.0f} Hz, "
            f"{band.mode_count} modes forment une {kind}{spacing}."
        )

    @staticmethod
    def _severity(score):
        if score >= 85:
            return "LOW"
        if score >= 60:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def _conclusion(score, dense_bands, sparse_bands):
        if score >= 85:
            return "La distribution modale est globalement régulière."

        details = []
        if dense_bands:
            details.append("des concentrations de modes")
        if sparse_bands:
            details.append("des zones modales clairsemées")

        phenomenon = " et ".join(details) or "des espacements irréguliers"
        return f"La distribution modale présente {phenomenon}."
