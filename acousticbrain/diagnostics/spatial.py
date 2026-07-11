from acousticbrain.models import (
    BinauralSpatialInterpretation,
    EvidenceLevel,
    SpatialStabilityStatus,
    SpeakerPairSpatialInterpretation,
)

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class SpatialDiagnostic(DiagnosticBase):
    """Présente exclusivement l'interprétation et les corrélations spatiales."""

    def analyze(self, context):
        spatial = context.spatial_analysis
        interpretation = context.spatial_interpretation
        correlations = context.spatial_correlation_analysis
        if spatial is None or interpretation is None:
            return Diagnostic(
                title="Analyse spatiale de paire",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.CALCULATED,
                message="Analyse spatiale indisponible ou paire incomplète.",
            )
        items = correlations.correlations if correlations is not None else []
        score = self._score(interpretation, items)
        conclusion = self._conclusion(interpretation, items)
        return Diagnostic(
            title="Analyse spatiale de paire",
            severity=self._severity(score),
            score=score,
            confidence=round(interpretation.confidence),
            evidence_level=EvidenceLevel.CALCULATED,
            message=conclusion,
            observations=self._observations(interpretation, items),
            conclusion=conclusion,
            causes=self._causes(interpretation, items),
            recommendations=self._recommendations(interpretation, items),
        )

    @staticmethod
    def _score(interpretation, correlations):
        penalty = 10.0 * len(correlations)
        if isinstance(interpretation, SpeakerPairSpatialInterpretation):
            if interpretation.technical_center_stability is SpatialStabilityStatus.UNSTABLE:
                penalty += 40.0
            elif interpretation.technical_center_stability is SpatialStabilityStatus.INDETERMINATE:
                penalty += 20.0
        return max(0.0, 100.0 - penalty)

    @staticmethod
    def _severity(score):
        if score >= 85:
            return "LOW"
        if score >= 60:
            return "MEDIUM"
        return "HIGH"

    @classmethod
    def _observations(cls, interpretation, correlations):
        if isinstance(interpretation, SpeakerPairSpatialInterpretation):
            observations = cls._speaker_observations(interpretation)
        else:
            observations = cls._binaural_observations(interpretation)
        observations.append(f"Corrélations spatiales structurées : {len(correlations)}.")
        observations.extend(
            f"Corrélation {item.code} : score {item.score:.0f}, confiance {item.confidence:.0f} %."
            for item in correlations
        )
        return observations

    @staticmethod
    def _speaker_observations(item):
        observations = [
            "Protocole : paire d'enceintes mesurée au même point.",
            f"Symétrie de niveau : {item.level_symmetry.value}.",
            f"Alignement temporel relatif : {item.relative_time_alignment.value}.",
            f"Cohérence de paire : {item.pair_coherence.value}.",
            f"Stabilité technique du centre : {item.technical_center_stability.value}.",
        ]
        if item.broadband_level_difference_db is not None:
            observations.append(
                f"Différence de niveau large bande : {item.broadband_level_difference_db:+.2f} dB."
            )
        if item.broadband_time_difference_ms is not None:
            observations.append(
                f"Différence temporelle large bande : {item.broadband_time_difference_ms:+.3f} ms."
            )
        if item.broadband_cross_correlation is not None:
            observations.append(
                f"Corrélation croisée large bande : {item.broadband_cross_correlation:.3f}."
            )
        frequencies = ", ".join(
            f"{frequency:.0f} Hz"
            for frequency in item.most_asymmetric_center_frequencies_hz
        )
        observations.append(
            "Bandes les plus asymétriques : "
            + (frequencies if frequencies else "aucune")
            + "."
        )
        return observations

    @staticmethod
    def _binaural_observations(item: BinauralSpatialInterpretation):
        observations = [
            "Protocole : paire binaurale.",
            f"Équilibre ILD : {item.interaural_level_balance.value}.",
            f"Alignement ITD : {item.interaural_time_alignment.value}.",
            f"Cohérence IACC : {item.interaural_coherence.value}.",
        ]
        for frequency, value in list(item.interaural_level_differences_db.items())[:5]:
            observations.append(f"ILD à {frequency:.0f} Hz : {value:+.2f} dB.")
        for frequency, value in list(item.interaural_time_differences_ms.items())[:5]:
            observations.append(f"ITD à {frequency:.0f} Hz : {value:+.3f} ms.")
        for frequency, value in list(item.interaural_cross_correlations.items())[:5]:
            observations.append(f"IACC à {frequency:.0f} Hz : {value:.3f}.")
        return observations

    @staticmethod
    def _conclusion(interpretation, correlations):
        if isinstance(interpretation, BinauralSpatialInterpretation):
            return "Les métriques interaurales sont présentées selon le protocole binaural déclaré."
        if interpretation.technical_center_stability is SpatialStabilityStatus.STABLE:
            return "La paire présente une stabilité technique du centre sur les faits disponibles."
        if interpretation.technical_center_stability is SpatialStabilityStatus.UNSTABLE:
            return "La paire présente des asymétries techniques de niveau, de temps ou de cohérence."
        return "La stabilité technique du centre reste indéterminée."

    @staticmethod
    def _causes(interpretation, correlations):
        return [item.code for item in correlations]

    @staticmethod
    def _recommendations(interpretation, correlations):
        if correlations:
            return [
                "Examiner les bandes et analyses sources des corrélations spatiales."
            ]
        return ["Conserver cette paire comme référence spatiale technique."]
