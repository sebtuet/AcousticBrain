from acousticbrain.models import EvidenceLevel, MeasurementReadinessStatus

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class MeasurementQualityDiagnostic(DiagnosticBase):
    """Restitue uniquement la qualité technique et la readiness mesurées."""

    def analyze(self, context):
        quality = context.measurement_quality_analysis
        readiness = context.measurement_readiness_analysis
        if quality is None or readiness is None:
            return Diagnostic(
                title="Qualité des mesures",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.CALCULATED,
                message="Qualité ou readiness des mesures indisponible.",
            )

        issues = [
            issue
            for channel in quality.channel_qualities
            for issue in channel.issues
        ]
        if quality.measurement_set_quality is not None:
            issues.extend(quality.measurement_set_quality.issues)
        blocked = [
            item for item in readiness.analyses
            if item.status is MeasurementReadinessStatus.BLOCKED
        ]
        reserved = [
            item for item in readiness.analyses
            if item.status is MeasurementReadinessStatus.AVAILABLE_WITH_RESERVATIONS
        ]
        conclusion = (
            "Certaines familles sont bloquées faute de preuves compatibles."
            if blocked
            else "Les mesures restent exploitables avec des réserves techniques."
            if reserved or issues
            else "Les mesures sont techniquement exploitables pour les familles évaluées."
        )
        observations = [
            f"Issues techniques structurées : {len(issues)}.",
            f"Familles bloquées : {len(blocked)}.",
            f"Familles disponibles avec réserves : {len(reserved)}.",
        ]
        observations.extend(
            f"Issue {issue.code.value} ({issue.scope.value})"
            + (f" — canal {issue.channel.value}" if issue.channel else "")
            + f", confiance {issue.confidence:.0f} %."
            for issue in issues
        )
        observations.extend(
            f"{item.family.value} : {item.status.value}, "
            f"confiance {item.confidence:.0f} %."
            for item in readiness.analyses
        )
        return Diagnostic(
            title="Qualité des mesures",
            severity="HIGH" if blocked else "MEDIUM" if reserved or issues else "LOW",
            confidence=round(min(quality.confidence, readiness.confidence)),
            evidence_level=EvidenceLevel.CALCULATED,
            message=conclusion,
            observations=observations,
            conclusion=conclusion,
            causes=list(dict.fromkeys(issue.code.value for issue in issues))
            + [f"{item.family.value}_BLOCKED" for item in blocked],
            recommendations=self._recommendations(issues),
        )

    @staticmethod
    def _recommendations(issues):
        codes = {issue.code.value for issue in issues}
        recommendations = []
        if "CLIPPING_DETECTED" in codes:
            recommendations.append("Reprendre les mesures écrêtées.")
        if codes & {"LOW_SIGNAL_LEVEL", "HIGH_NOISE_FLOOR", "INSUFFICIENT_DYNAMIC_RANGE"}:
            recommendations.append("Améliorer le rapport signal sur bruit avant une nouvelle mesure.")
        if "CHANNEL_TIMING_MISMATCH" in codes:
            recommendations.append("Corriger la synchronisation des canaux.")
        if "MISSING_REQUIRED_CHANNEL" in codes:
            recommendations.append("Compléter les canaux requis.")
        if "INCONSISTENT_MEASUREMENT_METADATA" in codes:
            recommendations.append("Vérifier et corriger les métadonnées des mesures.")
        return recommendations or ["Conserver les conditions de mesure actuelles."]
