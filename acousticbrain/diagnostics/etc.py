from acousticbrain.models import EvidenceLevel, ImpulseChannel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class ETCDiagnostic(DiagnosticBase):
    """Interprète les faits ETC et leurs corrélations déjà calculées."""

    DOMINANT_MINIMUM_LEVEL_DB = -20.0
    EARLY_MAXIMUM_DELAY_MS = 20.0
    RELIABLE_CORRELATION_CONFIDENCE = 70.0
    MAXIMUM_PRESENTED_EVENTS = 5

    def analyze(self, context):
        etc = context.etc_analysis
        correlations = context.etc_reflection_correlation_analysis
        if etc is None or not etc.available_channels:
            return Diagnostic(
                title="Réflexions temporelles précoces",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.OBSERVED,
                message="Analyse ETC indisponible.",
            )

        dominant = self._dominant_events(etc)
        unexplained = self._important_unmatched(correlations)
        score = self._score(etc, dominant, unexplained)
        conclusion = self._conclusion(etc, dominant, unexplained)
        return Diagnostic(
            title="Réflexions temporelles précoces",
            severity=self._severity(score),
            score=score,
            confidence=round(etc.confidence),
            evidence_level=EvidenceLevel.OBSERVED,
            message=conclusion,
            observations=self._observations(
                etc,
                correlations,
                dominant,
                unexplained,
            ),
            conclusion=conclusion,
            causes=self._causes(etc, correlations, unexplained),
            recommendations=self._recommendations(etc, unexplained),
        )

    @classmethod
    def _dominant_events(cls, etc):
        events = [
            (channel, event)
            for channel, analysis in etc.channels.items()
            for event in analysis.events
            if event.relative_level_db >= cls.DOMINANT_MINIMUM_LEVEL_DB
            and event.delay_ms <= cls.EARLY_MAXIMUM_DELAY_MS
        ]
        return sorted(events, key=lambda item: item[1].relative_level_db, reverse=True)

    @classmethod
    def _important_unmatched(cls, correlations):
        if correlations is None:
            return []
        events = [
            (channel, event)
            for channel, channel_events in correlations.unmatched_events.items()
            for event in channel_events
            if event.relative_level_db >= cls.DOMINANT_MINIMUM_LEVEL_DB
            and event.delay_ms <= cls.EARLY_MAXIMUM_DELAY_MS
        ]
        return sorted(events, key=lambda item: item[1].relative_level_db, reverse=True)

    @classmethod
    def _score(cls, etc, dominant, unexplained):
        event_penalty = min(40.0, len(dominant) * 5.0)
        unexplained_penalty = min(30.0, len(unexplained) * 5.0)
        event_total = (
            2 * etc.common_event_count
            + etc.left_only_event_count
            + etc.right_only_event_count
        )
        asymmetry = (
            (etc.left_only_event_count + etc.right_only_event_count) / event_total
            if event_total
            else 0.0
        )
        return max(
            0.0,
            100.0 - event_penalty - unexplained_penalty - 30.0 * asymmetry,
        )

    @staticmethod
    def _severity(score):
        if score >= 85:
            return "LOW"
        if score >= 60:
            return "MEDIUM"
        return "HIGH"

    @classmethod
    def _observations(cls, etc, correlations, dominant, unexplained):
        observations = [
            f"Canaux ETC disponibles : {len(etc.available_channels)}.",
            (
                f"Événements G-D communs : {etc.common_event_count} ; "
                f"spécifiques gauche : {etc.left_only_event_count} ; "
                f"spécifiques droite : {etc.right_only_event_count}."
            ),
            f"Réflexions dominantes avant 20 ms : {len(dominant)}.",
        ]
        observations.extend(
            cls._event_observation("Dominante", channel, event)
            for channel, event in dominant[: cls.MAXIMUM_PRESENTED_EVENTS]
        )
        if correlations is not None:
            reliable = [
                item
                for item in correlations.correlations
                if item.confidence >= cls.RELIABLE_CORRELATION_CONFIDENCE
            ]
            observations.append(
                f"Corrélations ETC-SBIR fiables : {len(reliable)}."
            )
            observations.extend(
                (
                    f"Surface candidate {item.surface.name} sur "
                    f"{item.channel.value} : délai mesuré "
                    f"{item.measured_delay_ms:.2f} ms, théorique "
                    f"{item.theoretical_delay_ms:.2f} ms, erreur "
                    f"{item.timing_error_ms:.2f} ms, confiance "
                    f"{item.confidence:.0f} %."
                )
                for item in reliable[: cls.MAXIMUM_PRESENTED_EVENTS]
            )
        observations.append(
            f"Événements importants non expliqués : {len(unexplained)}."
        )
        observations.extend(
            cls._event_observation("Non expliqué", channel, event)
            for channel, event in unexplained[: cls.MAXIMUM_PRESENTED_EVENTS]
        )
        return observations

    @staticmethod
    def _event_observation(kind, channel, event):
        return (
            f"{kind} {channel.value} à {event.delay_ms:.2f} ms : "
            f"{event.relative_level_db:.1f} dB, trajet supplémentaire "
            f"{event.acoustic_path_difference_m:.2f} m, confiance "
            f"{event.confidence:.0f} %."
        )

    @staticmethod
    def _conclusion(etc, dominant, unexplained):
        if unexplained:
            return "Des réflexions précoces dominantes restent sans explication structurée."
        if dominant:
            return "Des réflexions précoces dominantes ont été mesurées et rapprochées des faits disponibles."
        if etc.left_only_event_count or etc.right_only_event_count:
            return "Les réflexions précoces sont faibles, avec une asymétrie temporelle résiduelle."
        return "Aucune réflexion précoce dominante n'a été identifiée."

    @classmethod
    def _causes(cls, etc, correlations, unexplained):
        causes = []
        if etc.left_only_event_count or etc.right_only_event_count:
            causes.append("Événements temporels spécifiques à un canal")
        if correlations is not None:
            reliable_surfaces = {
                item.surface.name
                for item in correlations.correlations
                if item.confidence >= cls.RELIABLE_CORRELATION_CONFIDENCE
            }
            causes.extend(
                f"Réflexion compatible avec la surface {surface}"
                for surface in sorted(reliable_surfaces)
            )
        if unexplained:
            causes.append("Réflexions dominantes sans corrélation ETC-SBIR fiable")
        return causes

    @staticmethod
    def _recommendations(etc, unexplained):
        recommendations = []
        if etc.left_only_event_count or etc.right_only_event_count:
            recommendations.append(
                "Comparer les conditions temporelles des canaux gauche et droit."
            )
        if unexplained:
            recommendations.append(
                "Examiner les événements dominants non corrélés avant toute correction."
            )
        if not recommendations:
            recommendations.append(
                "Conserver la mesure ETC comme référence temporelle."
            )
        return recommendations

