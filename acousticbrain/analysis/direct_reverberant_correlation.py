from statistics import fmean

from acousticbrain.models import (
    ClarityAnalysis,
    DirectReverberantAnalysis,
    DirectReverberantCorrelation,
    DirectReverberantCorrelationAnalysis,
    ETCAnalysis,
    RT60Analysis,
    SpatialAnalysis,
)


class DirectReverberantCorrelationEngine:
    """Croise le D/R avec des connaissances structurées déjà calculées."""

    LOW_DRR_DB = 0.0
    FAVORABLE_DRR_DB = 3.0
    HIGH_RT60_S = 0.6
    DOMINANT_EVENT_LEVEL_DB = -20.0
    EARLY_EVENT_LIMIT_MS = 20.0
    MINIMUM_DOMINANT_EVENTS = 3
    DRR_CHANNEL_ASYMMETRY_DB = 3.0
    SPATIAL_LEVEL_ASYMMETRY_DB = 1.5
    HIGH_CLARITY_C50_DB = 3.0
    HIGH_DEFINITION_D50_PERCENT = 60.0

    def correlate(
        self,
        direct_reverberant: DirectReverberantAnalysis,
        rt60: RT60Analysis,
        etc: ETCAnalysis,
        clarity: ClarityAnalysis,
        spatial: SpatialAnalysis,
    ) -> DirectReverberantCorrelationAnalysis:
        correlations = [
            item
            for item in (
                self._low_drr_high_rt60(direct_reverberant, rt60),
                self._low_drr_dominant_early(direct_reverberant, etc),
                self._drr_spatial_asymmetry(direct_reverberant, spatial),
                self._favorable_drr_high_clarity(
                    direct_reverberant, clarity
                ),
            )
            if item is not None
        ]
        return DirectReverberantCorrelationAnalysis(
            correlations=correlations,
            source_analyses=(
                "DirectReverberantAnalysis",
                "RT60Analysis",
                "ETCAnalysis",
                "ClarityAnalysis",
                "SpatialAnalysis",
            ),
            confidence=(
                fmean(item.confidence for item in correlations)
                if correlations
                else 0.0
            ),
        )

    @classmethod
    def _low_drr_high_rt60(cls, drr, rt60):
        drr_bands = cls._drr_bands(drr)
        rt60_bands = cls._rt60_bands(rt60)
        centers = tuple(
            center
            for center in sorted(set(drr_bands).intersection(rt60_bands))
            if drr_bands[center].direct_to_reverberant_db < cls.LOW_DRR_DB
            and rt60_bands[center].rt60_seconds is not None
            and rt60_bands[center].rt60_seconds > cls.HIGH_RT60_S
        )
        if not centers:
            return None
        minimum_drr = min(
            drr_bands[center].direct_to_reverberant_db for center in centers
        )
        maximum_rt60 = max(
            rt60_bands[center].rt60_seconds for center in centers
        )
        return DirectReverberantCorrelation(
            code="LOW_DRR_HIGH_RT60",
            center_frequencies_hz=centers,
            source_metrics={
                "minimum_drr_db": minimum_drr,
                "maximum_rt60_s": maximum_rt60,
                "matched_band_count": float(len(centers)),
            },
            source_analyses=(
                "DirectReverberantAnalysis",
                "RT60Analysis",
            ),
            score=cls._paired_score(
                (cls.LOW_DRR_DB - minimum_drr) / 6.0,
                (maximum_rt60 - cls.HIGH_RT60_S) / cls.HIGH_RT60_S,
            ),
            confidence=cls._band_confidence(
                centers, drr_bands, rt60_bands
            ),
            technical_basis_codes=(
                "DRR_BELOW_THRESHOLD",
                "RT60_ABOVE_THRESHOLD",
            ),
        )

    @classmethod
    def _low_drr_dominant_early(cls, drr, etc):
        drr_bands = cls._drr_bands(drr)
        centers = tuple(
            center
            for center, band in sorted(drr_bands.items())
            if band.direct_to_reverberant_db < cls.LOW_DRR_DB
        )
        events = [
            event
            for analysis in etc.channels.values()
            for event in analysis.events
            if event.delay_ms <= cls.EARLY_EVENT_LIMIT_MS
            and event.relative_level_db >= cls.DOMINANT_EVENT_LEVEL_DB
        ]
        if not centers or len(events) < cls.MINIMUM_DOMINANT_EVENTS:
            return None
        return DirectReverberantCorrelation(
            code="LOW_DRR_DOMINANT_EARLY_REFLECTIONS",
            center_frequencies_hz=centers,
            source_metrics={
                "minimum_drr_db": min(
                    drr_bands[center].direct_to_reverberant_db
                    for center in centers
                ),
                "dominant_early_event_count": float(len(events)),
            },
            source_analyses=(
                "DirectReverberantAnalysis",
                "ETCAnalysis",
            ),
            score=min(
                100.0,
                50.0
                + 10.0 * (len(events) - cls.MINIMUM_DOMINANT_EVENTS),
            ),
            confidence=min(
                fmean(drr_bands[center].confidence for center in centers),
                etc.confidence,
                fmean(event.confidence for event in events),
            ),
            technical_basis_codes=(
                "DRR_BELOW_THRESHOLD",
                "DOMINANT_EARLY_EVENT_COUNT_ABOVE_THRESHOLD",
            ),
        )

    @classmethod
    def _drr_spatial_asymmetry(cls, drr, spatial):
        pair = spatial.pair_analysis
        if (
            pair is None
            or pair.broadband_level_difference_db is None
            or abs(pair.broadband_level_difference_db)
            < cls.SPATIAL_LEVEL_ASYMMETRY_DB
        ):
            return None
        differences = {
            center: difference
            for center, difference in (
                drr.left_right_direct_to_reverberant_differences_db.items()
            )
            if abs(difference) >= cls.DRR_CHANNEL_ASYMMETRY_DB
        }
        if not differences:
            return None
        maximum_drr_difference = max(abs(value) for value in differences.values())
        return DirectReverberantCorrelation(
            code="DRR_SPATIAL_CHANNEL_ASYMMETRY",
            center_frequencies_hz=tuple(sorted(differences)),
            source_metrics={
                "maximum_drr_channel_difference_db": maximum_drr_difference,
                "broadband_spatial_level_difference_db": (
                    pair.broadband_level_difference_db
                ),
            },
            source_analyses=(
                "DirectReverberantAnalysis",
                "SpatialAnalysis",
            ),
            score=cls._paired_score(
                maximum_drr_difference / cls.DRR_CHANNEL_ASYMMETRY_DB - 1.0,
                abs(pair.broadband_level_difference_db)
                / cls.SPATIAL_LEVEL_ASYMMETRY_DB
                - 1.0,
            ),
            confidence=min(drr.confidence, spatial.confidence),
            technical_basis_codes=(
                "DRR_CHANNEL_DIFFERENCE_ABOVE_THRESHOLD",
                "SPATIAL_LEVEL_DIFFERENCE_ABOVE_THRESHOLD",
            ),
        )

    @classmethod
    def _favorable_drr_high_clarity(cls, drr, clarity):
        drr_bands = cls._drr_bands(drr)
        clarity_bands = {
            band.center_frequency_hz: band for band in clarity.aggregate_bands
        }
        centers = tuple(
            center
            for center in sorted(set(drr_bands).intersection(clarity_bands))
            if drr_bands[center].direct_to_reverberant_db
            >= cls.FAVORABLE_DRR_DB
            and clarity_bands[center].c50_db is not None
            and clarity_bands[center].c50_db >= cls.HIGH_CLARITY_C50_DB
            and clarity_bands[center].d50_percent is not None
            and clarity_bands[center].d50_percent
            >= cls.HIGH_DEFINITION_D50_PERCENT
        )
        if not centers:
            return None
        return DirectReverberantCorrelation(
            code="FAVORABLE_DRR_HIGH_CLARITY",
            center_frequencies_hz=centers,
            source_metrics={
                "minimum_drr_db": min(
                    drr_bands[center].direct_to_reverberant_db
                    for center in centers
                ),
                "minimum_c50_db": min(
                    clarity_bands[center].c50_db for center in centers
                ),
                "minimum_d50_percent": min(
                    clarity_bands[center].d50_percent for center in centers
                ),
            },
            source_analyses=(
                "DirectReverberantAnalysis",
                "ClarityAnalysis",
            ),
            score=min(
                100.0,
                50.0 + 10.0 * len(centers),
            ),
            confidence=cls._band_confidence(
                centers, drr_bands, clarity_bands
            ),
            technical_basis_codes=(
                "DRR_ABOVE_FAVORABLE_THRESHOLD",
                "C50_ABOVE_THRESHOLD",
                "D50_ABOVE_THRESHOLD",
            ),
        )

    @staticmethod
    def _drr_bands(analysis):
        return {
            band.center_frequency_hz: band
            for band in analysis.aggregate_bands
            if band.direct_to_reverberant_db is not None
        }

    @staticmethod
    def _rt60_bands(analysis):
        return {
            band.center_frequency_hz: band for band in analysis.aggregate_bands
        }

    @staticmethod
    def _band_confidence(centers, first, second):
        return min(
            fmean(first[center].confidence for center in centers),
            fmean(second[center].confidence for center in centers),
        )

    @staticmethod
    def _paired_score(first_excess, second_excess):
        return min(
            100.0,
            50.0
            + 25.0
            * (min(1.0, first_excess) + min(1.0, second_excess)),
        )
