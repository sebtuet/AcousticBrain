from acousticbrain.models import EvidenceLevel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class BassDecayDiagnostic(DiagnosticBase):
    """Interprète uniquement les analyses Bass Decay structurées."""

    def analyze(self, context):
        analysis = context.bass_decay_analysis
        correlations = context.bass_decay_correlation_analysis
        if analysis is None or not analysis.aggregate_bands:
            return Diagnostic(
                title="Décroissance dans le grave",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.CALCULATED,
                message="Aucune bande Bass Decay commune n'est exploitable.",
            )
        items = correlations.correlations if correlations is not None else []
        maximum = max(
            band.estimated_decay_time_seconds
            for band in analysis.aggregate_bands
            if band.estimated_decay_time_seconds is not None
        )
        score = self._score(maximum, analysis.coverage)
        conclusion = self._conclusion(items)
        return Diagnostic(
            title="Décroissance dans le grave",
            severity=self._severity(score),
            score=score,
            confidence=round(analysis.confidence),
            evidence_level=EvidenceLevel.CALCULATED,
            message=conclusion,
            observations=self._observations(analysis, items, maximum),
            conclusion=conclusion,
            causes=[item.code for item in items],
            recommendations=self._recommendations(items),
        )

    @staticmethod
    def _score(maximum, coverage):
        duration_score = min(
            100.0,
            max(0.0, 100.0 * (2.0 - maximum) / 1.2),
        )
        return 0.7 * duration_score + 0.3 * coverage

    @staticmethod
    def _severity(score):
        if score >= 85.0:
            return "LOW"
        if score >= 60.0:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def _observations(analysis, correlations, maximum):
        observations = [
            f"Canaux Bass Decay disponibles : {len(analysis.available_channels)}.",
            f"Bandes communes exploitables : {len(analysis.aggregate_bands)}.",
            f"Couverture Bass Decay : {analysis.coverage:.0f} %.",
            f"Temps de décroissance maximal : {maximum:.3f} s.",
            "Écarts G-D Bass Decay significatifs : "
            f"{sum(abs(item.difference_seconds) >= 0.25 for item in analysis.left_right_band_differences)}.",
            f"Corrélations Bass Decay structurées : {len(correlations)}.",
        ]
        observations.extend(
            f"Bande {band.center_frequency_hz:.1f} Hz : "
            f"{band.estimated_decay_time_seconds:.3f} s, "
            f"confiance {band.confidence:.0f} %."
            for band in analysis.aggregate_bands
        )
        observations.extend(
            f"Corrélation {item.code} : score {item.score:.0f}, "
            f"confiance {item.confidence:.0f} %."
            for item in correlations
        )
        return observations

    @staticmethod
    def _conclusion(correlations):
        codes = {item.code for item in correlations}
        if "ASYMMETRIC_BASS_DECAY" in codes:
            return (
                "La décroissance basse fréquence présente des persistances "
                "structurées et des asymétries intercanales."
            )
        if correlations:
            return (
                "Des décroissances basses fréquences persistantes concordent "
                "avec d'autres faits acoustiques structurés."
            )
        return "Les bandes Bass Decay exploitables ne présentent aucune interaction structurée."

    @staticmethod
    def _recommendations(correlations):
        codes = {item.code for item in correlations}
        recommendations = []
        if codes & {
            "SLOW_DECAY_MODAL_INTERACTION",
            "SLOW_DECAY_RT60_INTERACTION",
            "LOW_DRR_LONG_BASS_DECAY",
        }:
            recommendations.append(
                "Examiner les bandes de décroissance longue avant toute correction."
            )
        if "SLOW_DECAY_MODAL_INTERACTION" in codes:
            recommendations.append(
                "Vérifier l'excitation modale aux fréquences concernées."
            )
        if "ASYMMETRIC_BASS_DECAY" in codes:
            recommendations.append(
                "Comparer les décroissances des canaux gauche et droit."
            )
        return recommendations or [
            "Conserver les mesures Bass Decay comme référence."
        ]
