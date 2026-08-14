from acousticbrain.models import EvidenceLevel, ImpulseChannel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class ClarityDiagnostic(DiagnosticBase):
    """Présente uniquement les faits de clarté et leurs corrélations."""

    CORRELATION_PENALTIES = {
        "LOW_CLARITY_HIGH_RT60": 20.0,
        "LOW_CLARITY_DENSE_EARLY_REFLECTIONS": 20.0,
        "CLARITY_ETC_CHANNEL_ASYMMETRY": 25.0,
        "HIGH_CENTER_TIME_LATE_DECAY": 20.0,
    }

    def analyze(self, context):
        clarity = context.clarity_analysis
        correlations = context.clarity_correlation_analysis
        if clarity is None or not clarity.available_channels:
            return Diagnostic(
                title="Clarté et définition",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.CALCULATED,
                message="Analyse de clarté indisponible.",
            )

        items = correlations.correlations if correlations is not None else []
        score = self._score(items)
        conclusion = self._conclusion(items)
        confidence = (
            correlations.confidence
            if correlations is not None and items
            else clarity.confidence
        )
        return Diagnostic(
            title="Clarté et définition",
            severity=self._severity(score),
            score=score,
            confidence=round(confidence),
            evidence_level=EvidenceLevel.CALCULATED,
            message=conclusion,
            observations=self._observations(clarity, items),
            conclusion=conclusion,
            causes=self._causes(items),
            recommendations=self._recommendations(items),
        )

    @staticmethod
    def _severity(score):
        if score >= 85:
            return "LOW"
        if score >= 60:
            return "MEDIUM"
        return "HIGH"

    @classmethod
    def _score(cls, correlations):
        penalty = sum(
            cls.CORRELATION_PENALTIES.get(item.code, 0.0)
            for item in correlations
        )
        return max(0.0, 100.0 - penalty)

    @classmethod
    def _observations(cls, clarity, correlations):
        observations = [
            f"Canaux de clarté disponibles : {len(clarity.available_channels)}.",
            f"Bandes de tiers d'octave communes : {len(clarity.aggregate_bands)}.",
        ]
        observations.extend(cls._channel_observations(clarity))
        observations.extend(cls._asymmetry_observations(clarity))
        observations.append(f"Corrélations temporelles structurées : {len(correlations)}.")
        observations.extend(
            (
                f"Corrélation {item.code} sur "
                f"{len(item.center_frequencies_hz)} bande(s) : "
                f"score {item.score:.0f}, confiance {item.confidence:.0f} %."
            )
            for item in correlations
        )
        return observations

    @classmethod
    def _channel_observations(cls, clarity):
        observations = []
        for channel in clarity.available_channels:
            analysis = clarity.channel_analyses.get(channel)
            if analysis is None:
                continue
            metrics = []
            if analysis.broadband_c50_db is not None:
                metrics.append(f"C50 {analysis.broadband_c50_db:.1f} dB")
            if analysis.broadband_c80_db is not None:
                metrics.append(f"C80 {analysis.broadband_c80_db:.1f} dB")
            if analysis.broadband_d50_percent is not None:
                metrics.append(f"D50 {analysis.broadband_d50_percent:.1f} %")
            if analysis.broadband_ts_s is not None:
                metrics.append(f"Ts {analysis.broadband_ts_s:.3f} s")
            if metrics:
                observations.append(
                    f"Canal {cls._channel_label(channel)} : "
                    + ", ".join(metrics)
                    + f", confiance {analysis.confidence:.0f} %."
                )
        return observations

    @staticmethod
    def _channel_label(channel):
        return {
            ImpulseChannel.LEFT: "gauche",
            ImpulseChannel.RIGHT: "droit",
            ImpulseChannel.STEREO: "L+R",
        }.get(channel, channel.value)

    @staticmethod
    def _asymmetry_observations(clarity):
        return [
            "Écarts G-D disponibles : "
            f"C50 {len(clarity.left_right_c50_differences_db)}, "
            f"C80 {len(clarity.left_right_c80_differences_db)}, "
            f"D50 {len(clarity.left_right_d50_differences_percent)}, "
            f"Ts {len(clarity.left_right_ts_differences_s)}.",
        ]

    @staticmethod
    def _conclusion(correlations):
        if correlations:
            return "Des corrélations temporelles structurées affectent les indicateurs de clarté."
        return "Aucune corrélation temporelle défavorable n'a franchi les seuils définis."

    @staticmethod
    def _causes(correlations):
        labels = {
            "LOW_CLARITY_HIGH_RT60": "Clarté faible associée à une décroissance RT60 longue",
            "LOW_CLARITY_DENSE_EARLY_REFLECTIONS": "Clarté faible associée à des réflexions précoces denses",
            "CLARITY_ETC_CHANNEL_ASYMMETRY": "Asymétries concordantes de clarté et d'événements ETC",
            "HIGH_CENTER_TIME_LATE_DECAY": "Temps central élevé associé à une énergie tardive persistante",
        }
        return [labels[item.code] for item in correlations if item.code in labels]

    @staticmethod
    def _recommendations(correlations):
        recommendations = []
        codes = {item.code for item in correlations}
        if "LOW_CLARITY_HIGH_RT60" in codes or "HIGH_CENTER_TIME_LATE_DECAY" in codes:
            recommendations.append(
                "Examiner les bandes où clarté et décroissance tardive sont corrélées."
            )
        if "LOW_CLARITY_DENSE_EARLY_REFLECTIONS" in codes:
            recommendations.append(
                "Examiner les réflexions précoces fortes dans les bandes concernées."
            )
        if "CLARITY_ETC_CHANNEL_ASYMMETRY" in codes:
            recommendations.append(
                "Comparer les conditions temporelles des canaux gauche et droit."
            )
        if not recommendations:
            recommendations.append(
                "Conserver les mesures de clarté comme référence temporelle."
            )
        return recommendations
