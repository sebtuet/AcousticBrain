from acousticbrain.models import EvidenceLevel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class RT60Diagnostic(DiagnosticBase):
    """Interprète uniquement l'agrégation RT60 déjà calculée."""

    MINIMUM_TARGET_SECONDS = 0.2
    MAXIMUM_TARGET_SECONDS = 0.4
    MINIMUM_RELIABLE_BAND_CONFIDENCE = 70.0
    SIGNIFICANT_DIFFERENCE_SECONDS = 0.2
    SEVERE_DIFFERENCE_SECONDS = 1.0
    SEVERE_DIFFERENCE_COUNT = 3

    def analyze(self, context):
        analysis = context.rt60_analysis
        if analysis is None or analysis.broadband_rt60_seconds is None:
            return Diagnostic(
                title="Réverbération RT60",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.CALCULATED,
                message="Analyse RT60 indisponible ou décroissance insuffisante.",
            )

        score = self._score(analysis)
        conclusion = self._conclusion(analysis, score)
        return Diagnostic(
            title="Réverbération RT60",
            severity=self._severity(score),
            score=score,
            confidence=round(analysis.confidence),
            evidence_level=EvidenceLevel.CALCULATED,
            message=conclusion,
            observations=self._observations(analysis),
            conclusion=conclusion,
            causes=self._causes(analysis),
            recommendations=self._recommendations(analysis),
        )

    @classmethod
    def _score(cls, analysis):
        rt60_score = cls._rt60_score(analysis.broadband_rt60_seconds)
        score = (
            rt60_score
            if analysis.interchannel_homogeneity is None
            else 0.7 * rt60_score + 0.3 * analysis.interchannel_homogeneity
        )
        significant = cls._significant_differences(analysis)
        if cls._has_severe_differences(significant):
            return min(score, 40.0)
        if significant:
            return min(score, 70.0)
        return score

    @classmethod
    def _rt60_score(cls, rt60_seconds):
        if cls.MINIMUM_TARGET_SECONDS <= rt60_seconds <= cls.MAXIMUM_TARGET_SECONDS:
            return 100.0
        if rt60_seconds < cls.MINIMUM_TARGET_SECONDS:
            return max(0.0, 100.0 * rt60_seconds / cls.MINIMUM_TARGET_SECONDS)
        return max(
            0.0,
            100.0
            * (1.0 - (rt60_seconds - cls.MAXIMUM_TARGET_SECONDS) / 0.6),
        )

    @staticmethod
    def _severity(score):
        if score >= 85:
            return "LOW"
        if score >= 60:
            return "MEDIUM"
        return "HIGH"

    @classmethod
    def _observations(cls, analysis):
        observations = [
            f"Canaux analysés : {len(analysis.available_channels)}.",
            f"Bandes de tiers d'octave communes : {len(analysis.aggregate_bands)}.",
            f"RT60 large bande agrégé : {analysis.broadband_rt60_seconds:.3f} s.",
        ]
        if (
            analysis.minimum_rt60_seconds is not None
            and analysis.maximum_rt60_seconds is not None
        ):
            observations.append(
                "Étendue intercanal large bande : "
                f"{analysis.minimum_rt60_seconds:.3f} à "
                f"{analysis.maximum_rt60_seconds:.3f} s."
            )
        if analysis.interchannel_homogeneity is not None:
            observations.append(
                "Homogénéité intercanal : "
                f"{analysis.interchannel_homogeneity:.0f} %."
            )
        significant = cls._significant_differences(analysis)
        unreliable = cls._unreliable_large_differences(analysis)
        observations.append(
            f"Écarts G-D fiables significatifs : {len(significant)}."
        )
        observations.extend(cls._difference_observation(item, True) for item in significant)
        observations.extend(cls._difference_observation(item, False) for item in unreliable)
        return observations

    @classmethod
    def _conclusion(cls, analysis, score):
        significant = cls._significant_differences(analysis)
        if cls._has_severe_differences(significant):
            return "La moyenne est maîtrisée, mais plusieurs bandes présentent des écarts intercanaux importants et fiables."
        if significant:
            return "La moyenne est maîtrisée, avec un écart intercanal fiable localisé."
        rt60 = analysis.broadband_rt60_seconds
        if rt60 < cls.MINIMUM_TARGET_SECONDS:
            return "La décroissance réverbérée mesurée est courte."
        if rt60 > cls.MAXIMUM_TARGET_SECONDS:
            return "La décroissance réverbérée mesurée est longue."
        if score < 85:
            return "La durée moyenne est maîtrisée, avec une hétérogénéité entre canaux."
        return "La durée et l'homogénéité de la réverbération sont maîtrisées."

    @classmethod
    def _causes(cls, analysis):
        causes = []
        rt60 = analysis.broadband_rt60_seconds
        if rt60 < cls.MINIMUM_TARGET_SECONDS:
            causes.append("Absorption importante dans la salle")
        if rt60 > cls.MAXIMUM_TARGET_SECONDS:
            causes.append("Décroissance énergétique prolongée")
        if (
            analysis.interchannel_homogeneity is not None
            and analysis.interchannel_homogeneity < 85
        ):
            causes.append("Décroissances différentes selon les canaux")
        if cls._significant_differences(analysis):
            causes.append("Écarts RT60 fiables dans certaines bandes")
        return causes

    @classmethod
    def _recommendations(cls, analysis):
        recommendations = []
        rt60 = analysis.broadband_rt60_seconds
        if rt60 < cls.MINIMUM_TARGET_SECONDS:
            recommendations.append(
                "Éviter d'ajouter de l'absorption sans vérifier les bandes concernées."
            )
        if rt60 > cls.MAXIMUM_TARGET_SECONDS:
            recommendations.append(
                "Examiner le traitement absorbant et la décroissance par bande."
            )
        if (
            analysis.interchannel_homogeneity is not None
            and analysis.interchannel_homogeneity < 85
        ):
            recommendations.append(
                "Comparer le placement et les surfaces réfléchissantes des deux canaux."
            )
        if cls._significant_differences(analysis):
            recommendations.append(
                "Examiner séparément les bandes présentant des écarts G-D fiables."
            )
        if analysis.confidence < 60:
            recommendations.append(
                "Répéter les mesures impulsionnelles pour renforcer la confiance."
            )
        if not recommendations:
            recommendations.append(
                "Conserver les conditions de mesure comme référence temporelle."
            )
        return recommendations

    @classmethod
    def _reliable_differences(cls, analysis):
        return [
            item
            for item in analysis.left_right_band_differences
            if item.confidence >= cls.MINIMUM_RELIABLE_BAND_CONFIDENCE
        ]

    @classmethod
    def _significant_differences(cls, analysis):
        return [
            item
            for item in cls._reliable_differences(analysis)
            if abs(item.difference_seconds) >= cls.SIGNIFICANT_DIFFERENCE_SECONDS
        ]

    @classmethod
    def _unreliable_large_differences(cls, analysis):
        return [
            item
            for item in analysis.left_right_band_differences
            if item.confidence < cls.MINIMUM_RELIABLE_BAND_CONFIDENCE
            and abs(item.difference_seconds) >= cls.SIGNIFICANT_DIFFERENCE_SECONDS
        ]

    @classmethod
    def _has_severe_differences(cls, differences):
        return (
            len(differences) >= cls.SEVERE_DIFFERENCE_COUNT
            or any(
                abs(item.difference_seconds) >= cls.SEVERE_DIFFERENCE_SECONDS
                for item in differences
            )
        )

    @staticmethod
    def _difference_observation(item, reliable):
        status = "fiable" if reliable else "non retenu, confiance insuffisante"
        return (
            f"Écart G-D {status} à {item.center_frequency_hz:.0f} Hz : "
            f"{item.difference_seconds:+.3f} s "
            f"(confiance {item.confidence:.0f} %, "
            f"méthodes {item.left_estimate}/{item.right_estimate})."
        )
