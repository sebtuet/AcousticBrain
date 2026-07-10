from acousticbrain.models import EvidenceLevel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class ConfidenceDiagnostic(DiagnosticBase):
    """Présente la confiance déjà agrégée par ConfidenceEngine."""

    def analyze(self, context):
        analysis = context.confidence_analysis

        if analysis is None:
            return Diagnostic(
                title="Confiance de l'analyse",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.CALCULATED,
                message="Analyse de confiance indisponible.",
            )

        conclusion = self._conclusion(analysis.score)

        return Diagnostic(
            title="Confiance de l'analyse",
            severity=self._severity(analysis.score),
            score=analysis.score,
            confidence=round(analysis.score),
            evidence_level=EvidenceLevel.CALCULATED,
            message=conclusion,
            observations=self._observations(analysis),
            conclusion=conclusion,
            causes=self._causes(analysis),
            recommendations=self._recommendations(analysis),
        )

    @staticmethod
    def _observations(analysis):
        observations = [
            (
                f"Preuves disponibles : {analysis.available_evidence_count} ; "
                f"indisponibles : {analysis.missing_evidence_count}."
            ),
            f"Couverture des preuves : {analysis.coverage_score:.0f} %.",
            f"Accord des confiances locales : {analysis.agreement_score:.0f} %.",
        ]
        observations.extend(
            (
                f"{factor.source} : {factor.score:.0f}/100 — "
                f"{factor.explanation}"
            )
            for factor in analysis.factors
        )
        return observations

    @staticmethod
    def _severity(score):
        if score >= 85:
            return "LOW"
        if score >= 60:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def _conclusion(score):
        if score >= 85:
            return "Les preuves disponibles soutiennent fortement les analyses."
        if score >= 60:
            return "Les analyses sont exploitables, avec certaines limites de couverture ou d'accord."
        return "Les analyses doivent être interprétées avec prudence."

    @staticmethod
    def _causes(analysis):
        causes = []
        if analysis.missing_evidence_count:
            causes.append("Certaines analyses ou confiances locales sont indisponibles")
        if analysis.agreement_score < 85:
            causes.append("Les confiances locales présentent une dispersion")
        return causes

    @staticmethod
    def _recommendations(analysis):
        recommendations = []
        if analysis.missing_evidence_count:
            recommendations.append("Compléter les analyses ou mesures indisponibles.")
        if analysis.agreement_score < 85:
            recommendations.append("Examiner les analyses dont la confiance locale est faible.")
        if not recommendations:
            recommendations.append("Conserver les conditions de mesure pour les analyses suivantes.")
        return recommendations
