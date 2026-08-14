from __future__ import annotations

from statistics import fmean

from acousticbrain.models import (
    ClarityAnalysis,
    ClarityCorrelation,
    ClarityCorrelationAnalysis,
    ETCAnalysis,
    RT60Analysis,
)


class ClarityCorrelationEngine:
    """Croise des analyses temporelles sans produire d'interprétation."""

    LOW_C50_DB = 0.0
    HIGH_RT60_S = 0.6
    HIGH_TS_S = 0.08
    LOW_D50_PERCENT = 50.0
    STRONG_EVENT_LEVEL_DB = -20.0
    EARLY_EVENT_LIMIT_MS = 50.0
    MINIMUM_STRONG_COMMON_EVENTS = 5
    C50_ASYMMETRY_DB = 2.0
    C80_ASYMMETRY_DB = 2.0
    D50_ASYMMETRY_PERCENT = 15.0
    TS_ASYMMETRY_S = 0.02
    ETC_EVENT_COUNT_ASYMMETRY = 3

    def correlate(
        self,
        clarity: ClarityAnalysis,
        rt60: RT60Analysis,
        etc: ETCAnalysis,
    ) -> ClarityCorrelationAnalysis:
        correlations = [
            correlation
            for correlation in (
                self._low_clarity_high_rt60(clarity, rt60),
                self._low_clarity_early_reflections(clarity, etc),
                self._clarity_etc_asymmetry(clarity, etc),
                self._high_ts_late_decay(clarity, rt60),
            )
            if correlation is not None
        ]
        return ClarityCorrelationAnalysis(
            correlations=correlations,
            source_analyses=(
                "ClarityAnalysis",
                "RT60Analysis",
                "ETCAnalysis",
            ),
            confidence=(
                fmean(correlation.confidence for correlation in correlations)
                if correlations
                else 0.0
            ),
        )

    @classmethod
    def _low_clarity_high_rt60(cls, clarity, rt60):
        clarity_bands = cls._clarity_bands(clarity)
        rt60_bands = cls._rt60_bands(rt60)
        centers = tuple(
            center
            for center in sorted(set(clarity_bands).intersection(rt60_bands))
            if clarity_bands[center].c50_db is not None
            and clarity_bands[center].c50_db < cls.LOW_C50_DB
            and rt60_bands[center].rt60_seconds is not None
            and rt60_bands[center].rt60_seconds > cls.HIGH_RT60_S
        )
        if not centers:
            return None
        c50_values = [clarity_bands[center].c50_db for center in centers]
        rt60_values = [rt60_bands[center].rt60_seconds for center in centers]
        return ClarityCorrelation(
            code="LOW_CLARITY_HIGH_RT60",
            center_frequencies_hz=centers,
            source_metrics={
                "minimum_c50_db": min(c50_values),
                "maximum_rt60_s": max(rt60_values),
                "matched_band_count": float(len(centers)),
            },
            source_analyses=("ClarityAnalysis", "RT60Analysis"),
            score=cls._paired_score(
                max((cls.LOW_C50_DB - value) / 10.0 for value in c50_values),
                max((value - cls.HIGH_RT60_S) / cls.HIGH_RT60_S for value in rt60_values),
            ),
            confidence=cls._band_confidence(
                centers, clarity_bands, rt60_bands
            ),
            technical_basis_codes=("C50_BELOW_THRESHOLD", "RT60_ABOVE_THRESHOLD"),
        )

    @classmethod
    def _low_clarity_early_reflections(cls, clarity, etc):
        clarity_bands = cls._clarity_bands(clarity)
        centers = tuple(
            center
            for center, band in sorted(clarity_bands.items())
            if band.c50_db is not None and band.c50_db < cls.LOW_C50_DB
        )
        strong_events = [
            pair
            for pair in etc.common_events
            if min(pair[0].delay_ms, pair[1].delay_ms) <= cls.EARLY_EVENT_LIMIT_MS
            and max(pair[0].relative_level_db, pair[1].relative_level_db)
            >= cls.STRONG_EVENT_LEVEL_DB
        ]
        if not centers or len(strong_events) < cls.MINIMUM_STRONG_COMMON_EVENTS:
            return None
        event_confidence = fmean(
            min(left.confidence, right.confidence)
            for left, right in strong_events
        )
        return ClarityCorrelation(
            code="LOW_CLARITY_DENSE_EARLY_REFLECTIONS",
            center_frequencies_hz=centers,
            source_metrics={
                "minimum_c50_db": min(clarity_bands[center].c50_db for center in centers),
                "strong_common_early_event_count": float(len(strong_events)),
            },
            source_analyses=("ClarityAnalysis", "ETCAnalysis"),
            score=min(
                100.0,
                50.0
                + 10.0 * (len(strong_events) - cls.MINIMUM_STRONG_COMMON_EVENTS),
            ),
            confidence=min(
                fmean(clarity_bands[center].confidence for center in centers),
                etc.confidence,
                event_confidence,
            ),
            technical_basis_codes=(
                "C50_BELOW_THRESHOLD",
                "COMMON_EARLY_EVENT_DENSITY_ABOVE_THRESHOLD",
            ),
        )

    @classmethod
    def _clarity_etc_asymmetry(cls, clarity, etc):
        asymmetric_centers = cls._asymmetric_centers(clarity)
        event_count_difference = abs(
            etc.left_only_event_count - etc.right_only_event_count
        )
        if (
            not asymmetric_centers
            or event_count_difference < cls.ETC_EVENT_COUNT_ASYMMETRY
        ):
            return None
        maximum_clarity_difference = max(
            cls._normalized_asymmetry(clarity, center)
            for center in asymmetric_centers
        )
        return ClarityCorrelation(
            code="CLARITY_ETC_CHANNEL_ASYMMETRY",
            center_frequencies_hz=asymmetric_centers,
            source_metrics={
                "maximum_normalized_clarity_difference": maximum_clarity_difference,
                "etc_specific_event_count_difference": float(event_count_difference),
            },
            source_analyses=("ClarityAnalysis", "ETCAnalysis"),
            score=min(
                100.0,
                50.0
                * max(
                    maximum_clarity_difference,
                    event_count_difference / cls.ETC_EVENT_COUNT_ASYMMETRY,
                ),
            ),
            confidence=min(clarity.confidence, etc.confidence),
            technical_basis_codes=(
                "CLARITY_CHANNEL_DIFFERENCE_ABOVE_THRESHOLD",
                "ETC_SPECIFIC_EVENT_IMBALANCE_ABOVE_THRESHOLD",
            ),
        )

    @classmethod
    def _high_ts_late_decay(cls, clarity, rt60):
        clarity_bands = cls._clarity_bands(clarity)
        rt60_bands = cls._rt60_bands(rt60)
        centers = tuple(
            center
            for center in sorted(set(clarity_bands).intersection(rt60_bands))
            if clarity_bands[center].ts_s is not None
            and clarity_bands[center].ts_s > cls.HIGH_TS_S
            and clarity_bands[center].d50_percent is not None
            and clarity_bands[center].d50_percent < cls.LOW_D50_PERCENT
            and rt60_bands[center].rt60_seconds is not None
            and rt60_bands[center].rt60_seconds > cls.HIGH_RT60_S
        )
        if not centers:
            return None
        return ClarityCorrelation(
            code="HIGH_CENTER_TIME_LATE_DECAY",
            center_frequencies_hz=centers,
            source_metrics={
                "maximum_ts_s": max(clarity_bands[center].ts_s for center in centers),
                "minimum_d50_percent": min(
                    clarity_bands[center].d50_percent for center in centers
                ),
                "maximum_rt60_s": max(
                    rt60_bands[center].rt60_seconds for center in centers
                ),
            },
            source_analyses=("ClarityAnalysis", "RT60Analysis"),
            score=cls._paired_score(
                max(clarity_bands[center].ts_s / cls.HIGH_TS_S - 1.0 for center in centers),
                max(rt60_bands[center].rt60_seconds / cls.HIGH_RT60_S - 1.0 for center in centers),
            ),
            confidence=cls._band_confidence(
                centers, clarity_bands, rt60_bands
            ),
            technical_basis_codes=(
                "TS_ABOVE_THRESHOLD",
                "D50_BELOW_THRESHOLD",
                "RT60_ABOVE_THRESHOLD",
            ),
        )

    @staticmethod
    def _clarity_bands(analysis):
        return {band.center_frequency_hz: band for band in analysis.aggregate_bands}

    @staticmethod
    def _rt60_bands(analysis):
        return {band.center_frequency_hz: band for band in analysis.aggregate_bands}

    @classmethod
    def _asymmetric_centers(cls, clarity):
        thresholds = (
            (clarity.left_right_c50_differences_db, cls.C50_ASYMMETRY_DB),
            (clarity.left_right_c80_differences_db, cls.C80_ASYMMETRY_DB),
            (
                clarity.left_right_d50_differences_percent,
                cls.D50_ASYMMETRY_PERCENT,
            ),
            (clarity.left_right_ts_differences_s, cls.TS_ASYMMETRY_S),
        )
        return tuple(
            sorted(
                {
                    center
                    for differences, threshold in thresholds
                    for center, difference in differences.items()
                    if abs(difference) >= threshold
                }
            )
        )

    @classmethod
    def _normalized_asymmetry(cls, clarity, center):
        ratios = []
        for differences, threshold in (
            (clarity.left_right_c50_differences_db, cls.C50_ASYMMETRY_DB),
            (clarity.left_right_c80_differences_db, cls.C80_ASYMMETRY_DB),
            (clarity.left_right_d50_differences_percent, cls.D50_ASYMMETRY_PERCENT),
            (clarity.left_right_ts_differences_s, cls.TS_ASYMMETRY_S),
        ):
            if center in differences:
                ratios.append(abs(differences[center]) / threshold)
        return max(ratios, default=0.0)

    @staticmethod
    def _paired_score(first_excess, second_excess):
        return min(100.0, 50.0 + 25.0 * (min(1.0, first_excess) + min(1.0, second_excess)))

    @staticmethod
    def _band_confidence(centers, first_bands, second_bands):
        return min(
            fmean(first_bands[center].confidence for center in centers),
            fmean(second_bands[center].confidence for center in centers),
        )
