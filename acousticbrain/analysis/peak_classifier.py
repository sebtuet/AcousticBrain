from acousticbrain.models import (
    EvidenceLevel,
    PeakClassification,
    PeakClassificationAnalysis,
    PeakClassificationType,
)


class PeakClassifier:
    """Classe les features détectées à partir de preuves physiques existantes."""

    def __init__(self, mode_tolerance_hz: float = 2.0):
        if mode_tolerance_hz < 0:
            raise ValueError("La tolérance modale doit être positive.")

        self.mode_tolerance_hz = mode_tolerance_hz

    def analyze(self, peaks, mode_matches, room_modes, sbir_analysis=None):
        classifications = [
            self._classify(peak, mode_matches, room_modes, sbir_analysis)
            for peak in peaks
        ]
        classified = [
            classification
            for classification in classifications
            if classification.classification is not PeakClassificationType.UNCLASSIFIED
        ]

        return PeakClassificationAnalysis(
            classifications=classifications,
            score=(100.0 * len(classified) / len(classifications)) if classifications else 0.0,
            confidence=(
                sum(classification.confidence for classification in classified)
                / len(classified)
                if classified
                else 0.0
            ),
        )

    def _classify(self, peak, mode_matches, room_modes, sbir_analysis):
        mode_match = self._mode_match_for(peak, mode_matches)
        if mode_match is not None:
            return PeakClassification(
                peak=peak,
                classification=PeakClassificationType.ROOM_MODE,
                confidence=mode_match.confidence,
                evidence_level=EvidenceLevel.CONFIRMED,
                explanation=(
                    f"Correspondance avec le mode axial {mode_match.mode.axis} "
                    f"ordre {mode_match.mode.order}"
                ),
                room_mode=mode_match.mode,
            )

        candidate = self._sbir_candidate_for(peak, sbir_analysis)
        if candidate is not None:
            return PeakClassification(
                peak=peak,
                classification=PeakClassificationType.SBIR,
                confidence=candidate.match_score,
                evidence_level=(
                    EvidenceLevel.CONFIRMED
                    if candidate.match_score >= 85
                    else EvidenceLevel.HYPOTHESIS
                ),
                explanation=(
                    "Correspondance avec une réflexion précoce sur "
                    f"{candidate.surface.name}"
                ),
                sbir_candidate=candidate,
            )

        mode = self._nearest_mode(peak, room_modes)
        if mode is not None:
            error_hz = abs(peak.frequency - mode.frequency)
            confidence = self._mode_confidence(error_hz)
            return PeakClassification(
                peak=peak,
                classification=PeakClassificationType.ROOM_MODE,
                confidence=confidence,
                evidence_level=EvidenceLevel.HYPOTHESIS,
                explanation=(
                    f"Proximité avec le mode axial {mode.axis} ordre {mode.order}"
                ),
                room_mode=mode,
            )

        return PeakClassification(
            peak=peak,
            classification=PeakClassificationType.UNCLASSIFIED,
            confidence=0.0,
            evidence_level=EvidenceLevel.OBSERVED,
            explanation="Aucune correspondance physique identifiée.",
        )

    @staticmethod
    def _mode_match_for(peak, mode_matches):
        return next((match for match in mode_matches if match.peak == peak), None)

    @staticmethod
    def _sbir_candidate_for(peak, sbir_analysis):
        if sbir_analysis is None:
            return None

        return next(
            (candidate for candidate in sbir_analysis.candidates if candidate.peak == peak),
            None,
        )

    def _nearest_mode(self, peak, room_modes):
        if not room_modes:
            return None

        mode = min(room_modes, key=lambda item: abs(item.frequency - peak.frequency))
        if abs(mode.frequency - peak.frequency) > self.mode_tolerance_hz:
            return None
        return mode

    def _mode_confidence(self, error_hz):
        if self.mode_tolerance_hz == 0:
            return 100.0
        return 100.0 * (1 - error_hz / self.mode_tolerance_hz)
