from acousticbrain.models import EvidenceLevel, HypothesisStatus

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class AcousticReasoningDiagnostic(DiagnosticBase):
    """Restitue les décisions du moteur sans réévaluer ses règles."""

    def analyze(self, context):
        analysis = context.acoustic_reasoning_analysis
        if analysis is None:
            return Diagnostic(
                title="Raisonnement acoustique déterministe",
                message="Aucune hypothèse structurée n'est disponible.",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.CALCULATED,
            )

        supported = tuple(
            item
            for item in analysis.hypotheses
            if item.status is HypothesisStatus.SUPPORTED
        )
        plausible = tuple(
            item
            for item in analysis.hypotheses
            if item.status is HypothesisStatus.PLAUSIBLE
        )
        conclusion = (
            "Des hypothèses acoustiques sont soutenues par des chaînes de "
            "preuves structurées."
            if supported
            else "Les hypothèses restent à vérifier avant toute correction."
        )
        recommendation_analysis = getattr(context, "recommendation_analysis", None)
        dispositions = {
            item.code: (item.status.value, item.status_reason)
            for item in (
                recommendation_analysis.recommendations
                if recommendation_analysis is not None else ()
            )
        }

        def recommendation_label(action):
            status, reason = dispositions.get(action.code, ("ACTIVE", None))
            suffix = (
                f" — {status}" + (f" ({reason})" if reason else "")
                if status != "ACTIVE" else ""
            )
            return f"{action.code} — {action.target}{suffix}."

        return Diagnostic(
            title="Raisonnement acoustique déterministe",
            message=conclusion,
            conclusion=conclusion,
            severity="HIGH" if supported else "MEDIUM" if plausible else "INFO",
            confidence=round(analysis.confidence),
            evidence_level=EvidenceLevel.CALCULATED,
            observations=[
                f"{item.code.value} : {item.status.value}, support "
                f"{item.support_score:.0f}/100, confiance "
                f"{item.confidence:.0f} %, preuves "
                f"{len(item.supporting_evidence)}, contre-preuves "
                f"{len(item.counter_evidence)}, faits manquants "
                f"{len(item.missing_facts)}."
                for item in analysis.hypotheses
            ],
            causes=[item.code.value for item in supported],
            recommendations=[
                recommendation_label(action)
                for item in analysis.hypotheses
                if item.status is not HypothesisStatus.CONTRADICTED
                for action in item.verification_actions
            ],
        )
