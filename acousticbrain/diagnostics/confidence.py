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

        readiness = getattr(context, "measurement_readiness_analysis", None)
        blocked = [
            item.family.value for item in getattr(readiness, "analyses", ())
            if item.status.value == "BLOCKED"
        ]
        reserved = [
            item.family.value for item in getattr(readiness, "analyses", ())
            if item.status.value == "AVAILABLE_WITH_RESERVATIONS"
        ]
        conclusion = self._conclusion(analysis.score, blocked, reserved)

        return Diagnostic(
            title="Confiance de l'analyse",
            severity=self._severity(analysis.score),
            score=analysis.score,
            confidence=round(analysis.score),
            evidence_level=EvidenceLevel.CALCULATED,
            message=conclusion,
            observations=self._observations(analysis, blocked, reserved),
            conclusion=conclusion,
            causes=self._causes(analysis),
            recommendations=self._recommendations(analysis),
            score_label="Confiance interne agrégée",
        )

    @staticmethod
    def _observations(analysis, blocked=(), reserved=()):
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
        observations.append(
            "Readiness des mesures : "
            + (f"{len(blocked)} famille(s) bloquée(s)" if blocked else f"{len(reserved)} famille(s) avec réserves" if reserved else "toutes les familles disponibles")
            + "."
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
    def _conclusion(score, blocked=(), reserved=()):
        if blocked:
            return (
                "La confiance des calculs internes est distincte de la readiness : "
                f"{', '.join(blocked)} sont bloquées. Les résultats associés "
                "restent provisoires jusqu'à correction des données d'entrée."
            )
        if reserved:
            return (
                "Les calculs internes sont exploitables, mais certaines familles "
                "restent disponibles avec des réserves de mesure."
            )
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
