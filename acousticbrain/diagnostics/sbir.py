from acousticbrain.models import EvidenceLevel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class SBIRDiagnostic(DiagnosticBase):

    def analyze(self, context):
        analysis = context.sbir
        geometry_correlations = getattr(
            context, "sbir_geometry_correlation_analysis", None
        )

        if (
            geometry_correlations is not None
            and geometry_correlations.best_match is not None
        ):
            return self._geometry_diagnostic(geometry_correlations)

        if analysis is None or analysis.best_match is None:
            return Diagnostic(
                title="Réflexions précoces",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.OBSERVED,
                message="Aucune correspondance exploitable avec une réflexion n'a été identifiée.",
            )

        candidate = analysis.best_match
        surface = self._surface_name(candidate.surface.name)
        severity = self._severity(analysis.score)
        evidence_level = (
            EvidenceLevel.CONFIRMED
            if analysis.confidence >= 85
            else EvidenceLevel.HYPOTHESIS
        )
        observations = [
            f"{len(analysis.candidates)} surfaces réfléchissantes ont été évaluées.",
            (
                f"Un creux à {candidate.measured_frequency:.1f} Hz "
                f"(prominence {candidate.peak.prominence:.1f} dB) correspond au "
                f"{surface}."
            ),
            f"Distance estimée : {candidate.distance_m:.2f} m.",
            f"Délai de réflexion estimé : {candidate.delay_ms:.1f} ms.",
        ]
        conclusion = (
            f"Le creux observé vers {candidate.measured_frequency:.0f} Hz est "
            f"compatible avec une réflexion sur le {surface} situé à environ "
            f"{candidate.distance_m:.2f} m de l'enceinte."
        )

        return Diagnostic(
            title="Réflexions précoces",
            severity=severity,
            score=analysis.score,
            confidence=round(analysis.confidence),
            evidence_level=evidence_level,
            message=conclusion,
            observations=observations,
            conclusion=conclusion,
            causes=[
                f"Réflexion précoce compatible avec le {surface}",
                "Distance réduite entre l'enceinte et une paroi",
            ],
            recommendations=[
                "Vérifier la distance entre l'enceinte et la paroi identifiée",
                "Tester un déplacement progressif de l'enceinte",
                "Confirmer la correspondance avec une mesure dédiée",
            ],
        )

    @staticmethod
    def _geometry_diagnostic(analysis):
        match = analysis.best_match
        candidate = match.candidate
        uncertainty = (
            f"{candidate.frequency_uncertainty_hz:.1f} Hz"
            if candidate.frequency_uncertainty_hz is not None
            else "indisponible"
        )
        geometry_confidence = (
            f"{candidate.confidence:.0f} %"
            if candidate.confidence is not None
            else "indisponible"
        )
        conclusion = (
            f"Le creux observé à {match.observed_dip.frequency:.1f} Hz est "
            f"compatible avec la prédiction SBIR de la surface "
            f"{candidate.surface_id}, sans attribution causale."
        )
        return Diagnostic(
            title="SBIR géométrique",
            severity="MEDIUM",
            score=100.0 - match.match_score,
            confidence=round(match.confidence),
            evidence_level=EvidenceLevel.HYPOTHESIS,
            message=conclusion,
            observations=[
                f"Surface candidate : {candidate.surface_id}.",
                f"Enceinte : {candidate.speaker_id} ; point d’écoute : "
                f"{candidate.listening_position_id}.",
                f"Trajet direct : {candidate.direct_path_m:.3f} m ; trajet "
                f"réfléchi : {candidate.reflected_path_m:.3f} m ; distance "
                f"supplémentaire : {candidate.extra_distance_m:.3f} m.",
                f"Annulation prédite : "
                f"{candidate.expected_cancellation_frequency_hz:.1f} Hz ; "
                f"creux observé : {match.observed_dip.frequency:.1f} Hz ; "
                f"écart : {match.frequency_error_hz:.1f} Hz "
                f"({match.frequency_error_percent:.1f} %).",
                f"Incertitude fréquentielle : {uncertainty} ; confiance "
                f"géométrique : {geometry_confidence}.",
                "Provenance géométrique : "
                + (", ".join(candidate.provenance_codes) or "indisponible")
                + ".",
            ],
            conclusion=conclusion,
            causes=[],
            recommendations=[],
        )

    @staticmethod
    def _severity(score):
        if score >= 85:
            return "LOW"
        if score >= 60:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def _surface_name(surface):
        return {
            "FRONT_WALL": "mur avant",
            "REAR_WALL": "mur arrière",
            "LEFT_WALL": "mur gauche",
            "RIGHT_WALL": "mur droit",
            "FLOOR": "sol",
            "CEILING": "plafond",
        }[surface]
