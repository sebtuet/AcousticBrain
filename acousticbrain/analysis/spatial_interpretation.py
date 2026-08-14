from __future__ import annotations

from acousticbrain.models import (
    BinauralSpatialInterpretation,
    SpatialAlignmentStatus,
    SpatialAnalysis,
    SpatialBalanceStatus,
    SpatialCoherenceStatus,
    SpatialMeasurementType,
    SpatialStabilityStatus,
    SpeakerPairSpatialInterpretation,
)


class SpatialInterpretationEngine:
    """Interprète uniquement les faits déjà présents dans SpatialAnalysis."""

    LEVEL_BALANCE_THRESHOLD_DB = 1.5
    TIME_ALIGNMENT_THRESHOLD_MS = 0.2
    COHERENT_THRESHOLD = 0.9
    PARTIAL_COHERENCE_THRESHOLD = 0.7
    MAXIMUM_ASYMMETRIC_BANDS = 5

    def interpret(
        self,
        analysis: SpatialAnalysis,
    ) -> SpeakerPairSpatialInterpretation | BinauralSpatialInterpretation | None:
        pair = analysis.pair_analysis
        if pair is None:
            return None
        if pair.measurement_type is SpatialMeasurementType.SPEAKER_CHANNEL_PAIR:
            return self._speaker_pair(pair)
        if pair.measurement_type is SpatialMeasurementType.BINAURAL_PAIR:
            return self._binaural_pair(pair)
        return None

    @classmethod
    def _speaker_pair(cls, pair):
        level_status = cls._balance_status(pair.broadband_level_difference_db)
        time_status = cls._alignment_status(pair.broadband_time_difference_ms)
        coherence_status = cls._coherence_status(
            pair.broadband_cross_correlation
        )
        return SpeakerPairSpatialInterpretation(
            measurement_type=pair.measurement_type,
            broadband_level_difference_db=pair.broadband_level_difference_db,
            broadband_time_difference_ms=pair.broadband_time_difference_ms,
            broadband_cross_correlation=pair.broadband_cross_correlation,
            level_symmetry=level_status,
            relative_time_alignment=time_status,
            pair_coherence=coherence_status,
            technical_center_stability=cls._stability_status(
                level_status,
                time_status,
                coherence_status,
            ),
            most_asymmetric_center_frequencies_hz=cls._asymmetric_bands(pair),
            confidence=pair.confidence,
        )

    @classmethod
    def _binaural_pair(cls, pair):
        ild = {
            band.center_frequency_hz: band.interaural_level_difference_db
            for band in pair.bands
            if band.interaural_level_difference_db is not None
        }
        itd = {
            band.center_frequency_hz: band.interaural_time_difference_ms
            for band in pair.bands
            if band.interaural_time_difference_ms is not None
        }
        iacc = {
            band.center_frequency_hz: band.iacc
            for band in pair.bands
            if band.iacc is not None
        }
        return BinauralSpatialInterpretation(
            measurement_type=pair.measurement_type,
            interaural_level_differences_db=ild,
            interaural_time_differences_ms=itd,
            interaural_cross_correlations=iacc,
            interaural_level_balance=cls._collection_balance_status(ild),
            interaural_time_alignment=cls._collection_alignment_status(itd),
            interaural_coherence=cls._collection_coherence_status(iacc),
            confidence=pair.confidence,
        )

    @classmethod
    def _asymmetric_bands(cls, pair):
        candidates = []
        for band in pair.bands:
            severities = []
            if band.level_difference_db is not None:
                severities.append(
                    abs(band.level_difference_db)
                    / cls.LEVEL_BALANCE_THRESHOLD_DB
                )
            if band.time_difference_ms is not None:
                severities.append(
                    abs(band.time_difference_ms)
                    / cls.TIME_ALIGNMENT_THRESHOLD_MS
                )
            if band.cross_correlation is not None:
                severities.append(
                    (1.0 - band.cross_correlation)
                    / (1.0 - cls.PARTIAL_COHERENCE_THRESHOLD)
                )
            severity = max(severities, default=0.0)
            if severity > 1.0:
                candidates.append((severity, band.center_frequency_hz))
        candidates.sort(key=lambda item: (-item[0], item[1]))
        return tuple(
            center
            for _, center in candidates[: cls.MAXIMUM_ASYMMETRIC_BANDS]
        )

    @classmethod
    def _balance_status(cls, value):
        if value is None:
            return SpatialBalanceStatus.UNAVAILABLE
        if abs(value) <= cls.LEVEL_BALANCE_THRESHOLD_DB:
            return SpatialBalanceStatus.BALANCED
        return SpatialBalanceStatus.ASYMMETRIC

    @classmethod
    def _alignment_status(cls, value):
        if value is None:
            return SpatialAlignmentStatus.UNAVAILABLE
        if abs(value) <= cls.TIME_ALIGNMENT_THRESHOLD_MS:
            return SpatialAlignmentStatus.ALIGNED
        return SpatialAlignmentStatus.OFFSET

    @classmethod
    def _coherence_status(cls, value):
        if value is None:
            return SpatialCoherenceStatus.UNAVAILABLE
        if value >= cls.COHERENT_THRESHOLD:
            return SpatialCoherenceStatus.COHERENT
        if value >= cls.PARTIAL_COHERENCE_THRESHOLD:
            return SpatialCoherenceStatus.PARTIAL
        return SpatialCoherenceStatus.WEAK

    @staticmethod
    def _stability_status(level, time, coherence):
        if (
            level is SpatialBalanceStatus.BALANCED
            and time is SpatialAlignmentStatus.ALIGNED
            and coherence is SpatialCoherenceStatus.COHERENT
        ):
            return SpatialStabilityStatus.STABLE
        if (
            level is SpatialBalanceStatus.UNAVAILABLE
            or time is SpatialAlignmentStatus.UNAVAILABLE
            or coherence is SpatialCoherenceStatus.UNAVAILABLE
        ):
            return SpatialStabilityStatus.INDETERMINATE
        return SpatialStabilityStatus.UNSTABLE

    @classmethod
    def _collection_balance_status(cls, values):
        if not values:
            return SpatialBalanceStatus.UNAVAILABLE
        if all(
            abs(value) <= cls.LEVEL_BALANCE_THRESHOLD_DB
            for value in values.values()
        ):
            return SpatialBalanceStatus.BALANCED
        return SpatialBalanceStatus.ASYMMETRIC

    @classmethod
    def _collection_alignment_status(cls, values):
        if not values:
            return SpatialAlignmentStatus.UNAVAILABLE
        if all(
            abs(value) <= cls.TIME_ALIGNMENT_THRESHOLD_MS
            for value in values.values()
        ):
            return SpatialAlignmentStatus.ALIGNED
        return SpatialAlignmentStatus.OFFSET

    @classmethod
    def _collection_coherence_status(cls, values):
        if not values:
            return SpatialCoherenceStatus.UNAVAILABLE
        return cls._coherence_status(min(values.values()))
