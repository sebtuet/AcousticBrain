from acousticbrain.models import EvidenceLevel, PeakClassificationType

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class PeakClassificationDiagnostic(DiagnosticBase):
    """Interprète les classifications déjà produites par PeakClassifier."""

    def analyze(self, context):
        analysis = context.peak_classification

        if analysis is None:
            return Diagnostic(
                title="Classification des pics",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.OBSERVED,
                message="Analyse de classification des pics indisponible.",
            )

        if not analysis.classifications:
            return Diagnostic(
                title="Classification des pics",
                severity="INFO",
                score=analysis.score,
                confidence=round(analysis.confidence),
                evidence_level=EvidenceLevel.OBSERVED,
                message="Aucun pic n'est disponible pour la classification.",
            )

        observations = self._observations(analysis)
        conclusion = self._conclusion(analysis)

        return Diagnostic(
            title="Classification des pics",
            severity=self._severity(analysis.score),
            score=analysis.score,
            confidence=round(analysis.confidence),
            evidence_level=self._evidence_level(analysis),
            message=conclusion,
            observations=observations,
            conclusion=conclusion,
            causes=self._causes(analysis),
            recommendations=self._recommendations(analysis),
        )

    @staticmethod
    def _observations(analysis):
        classifications = analysis.classifications
        counts = {
            classification_type: sum(
                item.classification is classification_type
                for item in classifications
            )
            for classification_type in PeakClassificationType
        }
        evidence_counts = {
            evidence_level: sum(
                item.evidence_level is evidence_level
                for item in classifications
            )
            for evidence_level in EvidenceLevel
        }

        observations = [
            (
                f"{len(classifications)} pics ont été évalués : "
                f"{PeakClassificationDiagnostic._label(counts[PeakClassificationType.ROOM_MODE], 'mode axial', 'modes axiaux')}, "
                f"{PeakClassificationDiagnostic._label(counts[PeakClassificationType.SBIR], 'candidat SBIR', 'candidats SBIR')}, "
                f"{PeakClassificationDiagnostic._label(counts[PeakClassificationType.UNCLASSIFIED], 'pic non classé', 'pics non classés')}."
            ),
            (
                "Niveaux de preuve : "
                f"{evidence_counts[EvidenceLevel.CONFIRMED]} confirmés, "
                f"{evidence_counts[EvidenceLevel.HYPOTHESIS]} hypothèses, "
                f"{evidence_counts[EvidenceLevel.OBSERVED]} observés."
            ),
        ]

        for item in classifications:
            if item.classification is PeakClassificationType.UNCLASSIFIED:
                continue
            observations.append(
                f"{item.peak.frequency:.1f} Hz : {item.explanation} "
                f"({item.confidence:.0f} %)."
            )

        return observations

    @staticmethod
    def _label(count, singular, plural):
        return f"{count} {singular if count == 1 else plural}"

    @staticmethod
    def _conclusion(analysis):
        classified_count = sum(
            item.classification is not PeakClassificationType.UNCLASSIFIED
            for item in analysis.classifications
        )

        return (
            f"{classified_count} pic(s) sur {len(analysis.classifications)} "
            "présentent une origine physique identifiée ou plausible."
        )

    @staticmethod
    def _evidence_level(analysis):
        levels = {item.evidence_level for item in analysis.classifications}
        if EvidenceLevel.CONFIRMED in levels:
            return EvidenceLevel.CONFIRMED
        if EvidenceLevel.HYPOTHESIS in levels:
            return EvidenceLevel.HYPOTHESIS
        return EvidenceLevel.OBSERVED

    @staticmethod
    def _severity(score):
        if score >= 85:
            return "LOW"
        if score >= 60:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def _causes(analysis):
        types = {item.classification for item in analysis.classifications}
        causes = []

        if PeakClassificationType.ROOM_MODE in types:
            causes.append("Modes axiaux de la pièce")
        if PeakClassificationType.SBIR in types:
            causes.append("Réflexions précoces identifiées")
        if PeakClassificationType.UNCLASSIFIED in types:
            causes.append("Phénomènes non classés à confirmer")

        return causes

    @staticmethod
    def _recommendations(analysis):
        types = {item.classification for item in analysis.classifications}
        recommendations = []

        if PeakClassificationType.ROOM_MODE in types:
            recommendations.append(
                "Évaluer le placement des enceintes et du point d'écoute."
            )
        if PeakClassificationType.SBIR in types:
            recommendations.append(
                "Vérifier les distances aux parois associées aux réflexions précoces."
            )
        if PeakClassificationType.UNCLASSIFIED in types:
            recommendations.append(
                "Compléter les mesures pour identifier les pics non classés."
            )

        return recommendations
