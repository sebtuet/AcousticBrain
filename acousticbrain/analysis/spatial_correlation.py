from statistics import fmean

from acousticbrain.models import (
    SpatialAlignmentStatus,
    SpatialBalanceStatus,
    SpatialCoherenceStatus,
    SpatialCorrelation,
    SpatialCorrelationAnalysis,
    SpatialStabilityStatus,
)


class SpatialCorrelationEngine:
    """Croise exclusivement des connaissances spatiales structurées."""

    LEVEL_DIFFERENCE_DB = 1.5
    TIME_DIFFERENCE_MS = 0.2
    ETC_EVENT_IMBALANCE = 3
    CLARITY_C50_DIFFERENCE_DB = 2.0
    CLARITY_C80_DIFFERENCE_DB = 2.0
    CLARITY_D50_DIFFERENCE_PERCENT = 15.0
    CLARITY_TS_DIFFERENCE_S = 0.02
    STEREO_AGREEMENT_SCORE = 85.0

    def correlate(self, spatial, interpretation, stereo, etc, clarity):
        correlations = []
        if interpretation is not None:
            for item in (
                self._level_and_stereo(interpretation, stereo),
                self._time_and_etc(interpretation, etc),
                self._coherence_and_clarity(interpretation, clarity),
                self._stable_agreement(interpretation, stereo, etc, clarity),
            ):
                if item is not None:
                    correlations.append(item)
        return SpatialCorrelationAnalysis(
            correlations=correlations,
            source_analyses=tuple(
                source
                for source in (
                    "SpatialAnalysis",
                    type(interpretation).__name__ if interpretation else None,
                    "StereoAnalysis",
                    "ETCAnalysis",
                    "ClarityAnalysis",
                )
                if source is not None
            ),
            confidence=(
                fmean(item.confidence for item in correlations)
                if correlations
                else 0.0
            ),
        )

    @classmethod
    def _level_and_stereo(cls, interpretation, stereo):
        level_status = cls._level_status(interpretation)
        balances = cls._stereo_balances(stereo)
        if level_status is not SpatialBalanceStatus.ASYMMETRIC or not balances:
            return None
        maximum = max(abs(value) for value in balances)
        if maximum < cls.LEVEL_DIFFERENCE_DB:
            return None
        level = cls._broadband_level(interpretation)
        return SpatialCorrelation(
            code="SPATIAL_LEVEL_STEREO_IMBALANCE",
            source_metrics={
                "broadband_level_difference_db": level,
                "maximum_stereo_balance_db": maximum,
            },
            source_analyses=(
                "SpatialAnalysis",
                type(interpretation).__name__,
                "StereoAnalysis",
            ),
            score=min(100.0, 50.0 + 10.0 * maximum),
            confidence=interpretation.confidence,
            technical_basis_codes=(
                "SPATIAL_LEVEL_ASYMMETRY",
                "STEREO_BALANCE_ASYMMETRY",
            ),
        )

    @classmethod
    def _time_and_etc(cls, interpretation, etc):
        if cls._time_status(interpretation) is not SpatialAlignmentStatus.OFFSET:
            return None
        imbalance = abs(etc.left_only_event_count - etc.right_only_event_count)
        if imbalance < cls.ETC_EVENT_IMBALANCE:
            return None
        return SpatialCorrelation(
            code="SPATIAL_TIME_ETC_CHANNEL_IMBALANCE",
            source_metrics={
                "broadband_time_difference_ms": cls._broadband_time(
                    interpretation
                ),
                "etc_specific_event_count_difference": float(imbalance),
            },
            source_analyses=(
                "SpatialAnalysis",
                type(interpretation).__name__,
                "ETCAnalysis",
            ),
            score=min(100.0, 50.0 + 10.0 * imbalance),
            confidence=min(interpretation.confidence, etc.confidence),
            technical_basis_codes=(
                "SPATIAL_TIME_OFFSET",
                "ETC_SPECIFIC_EVENT_IMBALANCE",
            ),
        )

    @classmethod
    def _coherence_and_clarity(cls, interpretation, clarity):
        if cls._coherence_status(interpretation) not in (
            SpatialCoherenceStatus.PARTIAL,
            SpatialCoherenceStatus.WEAK,
        ):
            return None
        centers, maximum = cls._clarity_asymmetry(clarity)
        if not centers:
            return None
        return SpatialCorrelation(
            code="SPATIAL_COHERENCE_CLARITY_ASYMMETRY",
            center_frequencies_hz=centers,
            source_metrics={"maximum_normalized_clarity_difference": maximum},
            source_analyses=(
                "SpatialAnalysis",
                type(interpretation).__name__,
                "ClarityAnalysis",
            ),
            score=min(100.0, 50.0 * maximum),
            confidence=min(interpretation.confidence, clarity.confidence),
            technical_basis_codes=(
                "PAIR_COHERENCE_BELOW_THRESHOLD",
                "CLARITY_CHANNEL_DIFFERENCE_ABOVE_THRESHOLD",
            ),
        )

    @classmethod
    def _stable_agreement(cls, interpretation, stereo, etc, clarity):
        if getattr(interpretation, "technical_center_stability", None) is not (
            SpatialStabilityStatus.STABLE
        ):
            return None
        _, clarity_maximum = cls._clarity_asymmetry(clarity)
        etc_imbalance = abs(
            etc.left_only_event_count - etc.right_only_event_count
        )
        if (
            stereo.symmetry_score < cls.STEREO_AGREEMENT_SCORE
            or etc_imbalance >= cls.ETC_EVENT_IMBALANCE
            or clarity_maximum > 1.0
        ):
            return None
        return SpatialCorrelation(
            code="SPATIAL_TECHNICAL_CENTER_AGREEMENT",
            source_metrics={
                "stereo_symmetry_score": stereo.symmetry_score,
                "etc_specific_event_count_difference": float(etc_imbalance),
                "maximum_normalized_clarity_difference": clarity_maximum,
            },
            source_analyses=(
                "SpatialAnalysis",
                type(interpretation).__name__,
                "StereoAnalysis",
                "ETCAnalysis",
                "ClarityAnalysis",
            ),
            score=stereo.symmetry_score,
            confidence=min(interpretation.confidence, etc.confidence, clarity.confidence),
            technical_basis_codes=(
                "TECHNICAL_CENTER_STABLE",
                "STRUCTURED_ANALYSES_AGREE",
            ),
        )

    @staticmethod
    def _stereo_balances(stereo):
        return [
            value
            for value in (stereo.balance_low, stereo.balance_mid, stereo.balance_high)
            if value is not None
        ]

    @classmethod
    def _clarity_asymmetry(cls, clarity):
        groups = (
            (clarity.left_right_c50_differences_db, cls.CLARITY_C50_DIFFERENCE_DB),
            (clarity.left_right_c80_differences_db, cls.CLARITY_C80_DIFFERENCE_DB),
            (clarity.left_right_d50_differences_percent, cls.CLARITY_D50_DIFFERENCE_PERCENT),
            (clarity.left_right_ts_differences_s, cls.CLARITY_TS_DIFFERENCE_S),
        )
        ratios = {
            center: max(
                abs(values[center]) / threshold
                for values, threshold in groups
                if center in values
            )
            for center in set().union(*(set(values) for values, _ in groups))
        }
        centers = tuple(sorted(center for center, ratio in ratios.items() if ratio > 1.0))
        return centers, max(ratios.values(), default=0.0)

    @staticmethod
    def _level_status(item):
        return (
            item.level_symmetry
            if hasattr(item, "level_symmetry")
            else item.interaural_level_balance
        )

    @staticmethod
    def _time_status(item):
        return (
            item.relative_time_alignment
            if hasattr(item, "relative_time_alignment")
            else item.interaural_time_alignment
        )

    @staticmethod
    def _coherence_status(item):
        return (
            item.pair_coherence
            if hasattr(item, "pair_coherence")
            else item.interaural_coherence
        )

    @staticmethod
    def _broadband_level(item):
        return getattr(item, "broadband_level_difference_db", 0.0) or 0.0

    @staticmethod
    def _broadband_time(item):
        return getattr(item, "broadband_time_difference_ms", 0.0) or 0.0
