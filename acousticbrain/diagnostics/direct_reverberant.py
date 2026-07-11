from acousticbrain.models import EvidenceLevel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class DirectReverberantDiagnostic(DiagnosticBase):
    """Interprète uniquement les analyses D/R structurées existantes."""

    LOW_DRR_DB = 0.0
    SIGNIFICANT_CHANNEL_DIFFERENCE_DB = 3.0

    def analyze(self, context):
        analysis = context.direct_reverberant_analysis
        correlations = context.direct_reverberant_correlation_analysis
        if (
            analysis is None
            or analysis.broadband_direct_to_reverberant_db is None
        ):
            return Diagnostic(
                title="Rapport direct / réverbéré",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.CALCULATED,
                message="Analyse D/R indisponible ou énergie insuffisante.",
            )
        items = correlations.correlations if correlations is not None else []
        score = self._score(analysis, items)
        conclusion = self._conclusion(analysis, items)
        return Diagnostic(
            title="Rapport direct / réverbéré",
            severity=self._severity(score),
            score=score,
            confidence=round(analysis.confidence),
            evidence_level=EvidenceLevel.CALCULATED,
            message=conclusion,
            observations=self._observations(analysis, items),
            conclusion=conclusion,
            causes=[item.code for item in items],
            recommendations=self._recommendations(analysis, items),
        )

    @classmethod
    def _score(cls, analysis, correlations):
        broadband = analysis.broadband_direct_to_reverberant_db
        base = min(100.0, max(0.0, 50.0 + 50.0 * broadband / 6.0))
        adverse_count = sum(
            item.code != "FAVORABLE_DRR_HIGH_CLARITY"
            for item in correlations
        )
        return max(0.0, base - 10.0 * adverse_count)

    @staticmethod
    def _severity(score):
        if score >= 85:
            return "LOW"
        if score >= 60:
            return "MEDIUM"
        return "HIGH"

    @classmethod
    def _observations(cls, analysis, correlations):
        observations = [
            f"Canaux D/R disponibles : {len(analysis.available_channels)}.",
            f"Bandes communes exploitables : {len(analysis.aggregate_bands)}.",
            "D/R large bande agrégé : "
            f"{analysis.broadband_direct_to_reverberant_db:+.2f} dB.",
        ]
        for channel in analysis.available_channels:
            channel_analysis = analysis.channel_analyses[channel]
            value = channel_analysis.broadband_direct_to_reverberant_db
            if value is not None:
                observations.append(
                    f"Canal {channel.value} : D/R {value:+.2f} dB, "
                    f"confiance {channel_analysis.confidence:.0f} %."
                )
        significant = {
            center: difference
            for center, difference in (
                analysis.left_right_direct_to_reverberant_differences_db.items()
            )
            if abs(difference) >= cls.SIGNIFICANT_CHANNEL_DIFFERENCE_DB
        }
        observations.append(
            f"Écarts G-D D/R significatifs : {len(significant)}."
        )
        observations.extend(
            f"Écart D/R G-D à {center:.0f} Hz : {difference:+.2f} dB."
            for center, difference in sorted(significant.items())
        )
        observations.append(
            f"Corrélations D/R structurées : {len(correlations)}."
        )
        observations.extend(
            f"Corrélation {item.code} : score {item.score:.0f}, "
            f"confiance {item.confidence:.0f} %."
            for item in correlations
        )
        return observations

    @classmethod
    def _conclusion(cls, analysis, correlations):
        if analysis.broadband_direct_to_reverberant_db < cls.LOW_DRR_DB:
            return "L'énergie réverbérée domine l'énergie directe sur l'agrégat large bande."
        if correlations:
            return "Le rapport D/R large bande est favorable, avec des interactions locales structurées."
        return "L'énergie directe domine l'énergie réverbérée sur les faits disponibles."

    @classmethod
    def _recommendations(cls, analysis, correlations):
        if analysis.broadband_direct_to_reverberant_db < cls.LOW_DRR_DB:
            return [
                "Examiner les bandes et corrélations où l'énergie directe est insuffisante."
            ]
        if correlations:
            return [
                "Examiner les interactions D/R locales avant toute modification."
            ]
        return ["Conserver les fenêtres énergétiques comme référence."]
