from __future__ import annotations

from statistics import fmean
from typing import TYPE_CHECKING

from acousticbrain.models import (
    ClarityAnalysis,
    ClarityCorrelationAnalysis,
    DirectReverberantAnalysis,
    DirectReverberantCorrelationAnalysis,
    ETCAnalysis,
    ETCReflectionCorrelationAnalysis,
    GlobalAnalysis,
    GlobalCorrelation,
    GlobalDomainAnalysis,
    ModalDensityAnalysis,
    RT60Analysis,
    SBIRAnalysis,
    SpatialAnalysis,
    SpatialCorrelationAnalysis,
    StereoAnalysis,
)
from acousticbrain.knowledge_codes import (
    GlobalCorrelationCode,
    GlobalDomainCode,
    SourceAnalysisCode,
)

if TYPE_CHECKING:
    from acousticbrain.models import ConfidenceAnalysis, PeakClassificationAnalysis


class GlobalSynthesizer:
    """Agrège exclusivement des connaissances d'analyse structurées."""

    PRIORITY_SCORE_THRESHOLD = 85.0
    RT60_MINIMUM_TARGET_S = 0.2
    RT60_MAXIMUM_TARGET_S = 0.4
    RT60_EXCESS_RANGE_S = 0.6
    CLARITY_CORRELATION_PENALTY = 20.0
    SPATIAL_CORRELATION_PENALTY = 30.0
    DRR_CORRELATION_PENALTY = 20.0

    def synthesize(
        self,
        *,
        stereo: StereoAnalysis | None = None,
        sbir: SBIRAnalysis | None = None,
        modal_density: ModalDensityAnalysis | None = None,
        peak_classification: PeakClassificationAnalysis | None = None,
        rt60: RT60Analysis | None = None,
        etc: ETCAnalysis | None = None,
        clarity: ClarityAnalysis | None = None,
        spatial: SpatialAnalysis | None = None,
        clarity_correlations: ClarityCorrelationAnalysis | None = None,
        spatial_correlations: SpatialCorrelationAnalysis | None = None,
        etc_reflection_correlations: (
            ETCReflectionCorrelationAnalysis | None
        ) = None,
        direct_reverberant: DirectReverberantAnalysis | None = None,
        direct_reverberant_correlations: (
            DirectReverberantCorrelationAnalysis | None
        ) = None,
        confidence: ConfidenceAnalysis | None = None,
    ) -> GlobalAnalysis:
        domains = self._domains(
            stereo=stereo,
            sbir=sbir,
            modal_density=modal_density,
            peak_classification=peak_classification,
            rt60=rt60,
            etc=etc,
            clarity=clarity,
            spatial=spatial,
            clarity_correlations=clarity_correlations,
            spatial_correlations=spatial_correlations,
            etc_reflection_correlations=etc_reflection_correlations,
            direct_reverberant=direct_reverberant,
            direct_reverberant_correlations=(
                direct_reverberant_correlations
            ),
        )
        local_confidences = [
            domain.confidence
            for domain in domains
            if domain.confidence is not None
        ]

        return GlobalAnalysis(
            score=fmean(domain.score for domain in domains) if domains else None,
            confidence=(
                confidence.score
                if confidence is not None
                else fmean(local_confidences) if local_confidences else None
            ),
            domains=domains,
            correlations=self._correlations(
                domains,
                peak_classification,
                clarity_correlations,
                spatial_correlations,
                direct_reverberant_correlations,
            ),
            priority_domains=tuple(
                domain.code
                for domain in sorted(domains, key=lambda item: item.score)
                if domain.score < self.PRIORITY_SCORE_THRESHOLD
            ),
            source_analyses=tuple(domain.source_analysis for domain in domains),
        )

    @classmethod
    def _domains(
        cls,
        *,
        stereo: StereoAnalysis | None,
        sbir: SBIRAnalysis | None,
        modal_density: ModalDensityAnalysis | None,
        peak_classification: PeakClassificationAnalysis | None,
        rt60: RT60Analysis | None,
        etc: ETCAnalysis | None,
        clarity: ClarityAnalysis | None,
        spatial: SpatialAnalysis | None,
        clarity_correlations: ClarityCorrelationAnalysis | None,
        spatial_correlations: SpatialCorrelationAnalysis | None,
        etc_reflection_correlations: ETCReflectionCorrelationAnalysis | None,
        direct_reverberant: DirectReverberantAnalysis | None,
        direct_reverberant_correlations: (
            DirectReverberantCorrelationAnalysis | None
        ),
    ) -> list[GlobalDomainAnalysis]:
        domains: list[GlobalDomainAnalysis] = []

        if stereo is not None:
            score = stereo.symmetry_score
            domains.append(
                GlobalDomainAnalysis(
                    code="STEREO",
                    score=score,
                    confidence=None,
                    source_analysis="StereoAnalysis",
                    recommendation_codes=(
                        ("CHECK_STEREO_PLACEMENT",)
                        if score < cls.PRIORITY_SCORE_THRESHOLD
                        else ()
                    ),
                )
            )
        if sbir is not None:
            domains.append(
                GlobalDomainAnalysis(
                    code="SBIR",
                    score=sbir.score,
                    confidence=sbir.confidence,
                    source_analysis="SBIRAnalysis",
                    recommendation_codes=(
                        ("TEST_SPEAKER_DISTANCE",)
                        if sbir.score < cls.PRIORITY_SCORE_THRESHOLD
                        else ()
                    ),
                )
            )
        if modal_density is not None:
            domains.append(
                GlobalDomainAnalysis(
                    code="MODAL_DENSITY",
                    score=modal_density.score,
                    confidence=modal_density.confidence,
                    source_analysis="ModalDensityAnalysis",
                    recommendation_codes=(
                        ("MEASURE_MULTIPLE_POSITIONS",)
                        if modal_density.score < cls.PRIORITY_SCORE_THRESHOLD
                        else ()
                    ),
                )
            )
        if peak_classification is not None:
            unclassified_count = sum(
                cls._classification_code(item) == "UNCLASSIFIED"
                for item in peak_classification.classifications
            )
            domains.append(
                GlobalDomainAnalysis(
                    code="PEAK_CLASSIFICATION",
                    score=peak_classification.score,
                    confidence=peak_classification.confidence,
                    source_analysis="PeakClassificationAnalysis",
                    recommendation_codes=(
                        ("INVESTIGATE_UNCLASSIFIED_PEAKS",)
                        if unclassified_count
                        else ()
                    ),
                )
            )

        rt60_domain = cls._rt60_domain(rt60)
        if rt60_domain is not None:
            domains.append(rt60_domain)

        etc_domain = cls._etc_domain(etc, etc_reflection_correlations)
        if etc_domain is not None:
            domains.append(etc_domain)

        clarity_domain = cls._correlation_domain(
            analysis=clarity,
            correlations=clarity_correlations,
            code=GlobalDomainCode.CLARITY,
            source=SourceAnalysisCode.CLARITY,
            penalty=cls.CLARITY_CORRELATION_PENALTY,
        )
        if clarity_domain is not None:
            domains.append(clarity_domain)

        spatial_domain = cls._correlation_domain(
            analysis=spatial,
            correlations=spatial_correlations,
            code=GlobalDomainCode.SPATIAL,
            source=SourceAnalysisCode.SPATIAL,
            penalty=cls.SPATIAL_CORRELATION_PENALTY,
            available=(
                spatial is not None and spatial.pair_analysis is not None
            ),
        )
        if spatial_domain is not None:
            domains.append(spatial_domain)

        drr_domain = cls._direct_reverberant_domain(
            direct_reverberant,
            direct_reverberant_correlations,
        )
        if drr_domain is not None:
            domains.append(drr_domain)

        return domains

    @classmethod
    def _direct_reverberant_domain(cls, analysis, correlations):
        if (
            analysis is None
            or analysis.broadband_direct_to_reverberant_db is None
            or correlations is None
        ):
            return None
        base_score = 50.0 + (
            50.0 * analysis.broadband_direct_to_reverberant_db / 6.0
        )
        adverse_count = sum(
            item.code != "FAVORABLE_DRR_HIGH_CLARITY"
            for item in correlations.correlations
        )
        score = base_score - (
            cls.DRR_CORRELATION_PENALTY * adverse_count
        )
        return GlobalDomainAnalysis(
            code=GlobalDomainCode.DIRECT_REVERBERANT,
            score=min(100.0, max(0.0, score)),
            confidence=analysis.confidence,
            source_analysis=SourceAnalysisCode.DIRECT_REVERBERANT,
        )

    @classmethod
    def _rt60_domain(cls, analysis):
        if analysis is None or analysis.broadband_rt60_seconds is None:
            return None
        duration = analysis.broadband_rt60_seconds
        if cls.RT60_MINIMUM_TARGET_S <= duration <= cls.RT60_MAXIMUM_TARGET_S:
            duration_score = 100.0
        elif duration < cls.RT60_MINIMUM_TARGET_S:
            duration_score = 100.0 * duration / cls.RT60_MINIMUM_TARGET_S
        else:
            duration_score = 100.0 * (
                1.0
                - (duration - cls.RT60_MAXIMUM_TARGET_S)
                / cls.RT60_EXCESS_RANGE_S
            )
        duration_score = min(100.0, max(0.0, duration_score))
        score = (
            duration_score
            if analysis.interchannel_homogeneity is None
            else 0.7 * duration_score
            + 0.3 * analysis.interchannel_homogeneity
        )
        return GlobalDomainAnalysis(
            code=GlobalDomainCode.RT60,
            score=min(100.0, max(0.0, score)),
            confidence=analysis.confidence,
            source_analysis=SourceAnalysisCode.RT60,
        )

    @staticmethod
    def _etc_domain(analysis, correlations):
        if (
            analysis is None
            or not analysis.available_channels
            or correlations is None
            or correlations.evaluated_event_count <= 0
        ):
            return None
        explained = (
            correlations.matched_event_count
            / correlations.evaluated_event_count
        )
        event_total = (
            2 * analysis.common_event_count
            + analysis.left_only_event_count
            + analysis.right_only_event_count
        )
        asymmetry = (
            (analysis.left_only_event_count + analysis.right_only_event_count)
            / event_total
            if event_total
            else 0.0
        )
        score = 100.0 * (0.7 * explained + 0.3 * (1.0 - asymmetry))
        return GlobalDomainAnalysis(
            code=GlobalDomainCode.ETC,
            score=min(100.0, max(0.0, score)),
            confidence=min(analysis.confidence, correlations.confidence),
            source_analysis=SourceAnalysisCode.ETC,
        )

    @staticmethod
    def _correlation_domain(
        *,
        analysis,
        correlations,
        code,
        source,
        penalty,
        available=True,
    ):
        if analysis is None or correlations is None or not available:
            return None
        score = max(0.0, 100.0 - penalty * len(correlations.correlations))
        return GlobalDomainAnalysis(
            code=code,
            score=score,
            confidence=analysis.confidence,
            source_analysis=source,
        )

    @classmethod
    def _correlations(
        cls,
        domains: list[GlobalDomainAnalysis],
        peak_classification: PeakClassificationAnalysis | None,
        clarity_correlations: ClarityCorrelationAnalysis | None,
        spatial_correlations: SpatialCorrelationAnalysis | None,
        direct_reverberant_correlations: (
            DirectReverberantCorrelationAnalysis | None
        ),
    ) -> list[GlobalCorrelation]:
        by_code = {domain.code: domain for domain in domains}
        correlations: list[GlobalCorrelation] = []

        stereo = by_code.get("STEREO")
        sbir = by_code.get("SBIR")
        if cls._both_priorities(stereo, sbir):
            correlations.append(
                cls._correlation(
                    "STEREO_SBIR_PLACEMENT_INTERACTION",
                    stereo,
                    sbir,
                )
            )

        modal = by_code.get("MODAL_DENSITY")
        peaks = by_code.get("PEAK_CLASSIFICATION")
        has_modal_peaks = (
            peak_classification is not None
            and any(
                cls._classification_code(item) == "ROOM_MODE"
                for item in peak_classification.classifications
            )
        )
        if cls._both_priorities(modal, peaks) and has_modal_peaks:
            correlations.append(
                cls._correlation(
                    "MODAL_DENSITY_PEAK_INTERACTION",
                    modal,
                    peaks,
                )
            )

        cls._new_correlations(
            correlations,
            by_code,
            clarity_correlations,
            spatial_correlations,
            direct_reverberant_correlations,
        )

        return correlations

    @classmethod
    def _new_correlations(
        cls,
        result,
        domains,
        clarity_correlations,
        spatial_correlations,
        direct_reverberant_correlations,
    ):
        clarity_codes = cls._codes(clarity_correlations)
        spatial_codes = cls._codes(spatial_correlations)
        drr_codes = cls._codes(direct_reverberant_correlations)
        rules = (
            (
                GlobalCorrelationCode.ETC_SPATIAL_ASYMMETRY,
                GlobalDomainCode.ETC,
                GlobalDomainCode.SPATIAL,
                bool(
                    spatial_codes
                    & {
                        "SPATIAL_LEVEL_STEREO_IMBALANCE",
                        "SPATIAL_TIME_ETC_CHANNEL_IMBALANCE",
                    }
                ),
                SourceAnalysisCode.SPATIAL_CORRELATION,
            ),
            (
                GlobalCorrelationCode.RT60_CLARITY_DECAY_INTERACTION,
                GlobalDomainCode.RT60,
                GlobalDomainCode.CLARITY,
                bool(
                    clarity_codes
                    & {
                        "LOW_CLARITY_HIGH_RT60",
                        "HIGH_CENTER_TIME_LATE_DECAY",
                    }
                ),
                SourceAnalysisCode.CLARITY_CORRELATION,
            ),
            (
                GlobalCorrelationCode.ETC_CLARITY_EARLY_ENERGY_INTERACTION,
                GlobalDomainCode.ETC,
                GlobalDomainCode.CLARITY,
                "LOW_CLARITY_DENSE_EARLY_REFLECTIONS" in clarity_codes,
                SourceAnalysisCode.CLARITY_CORRELATION,
            ),
            (
                GlobalCorrelationCode.SPATIAL_STEREO_ALIGNMENT,
                GlobalDomainCode.SPATIAL,
                "STEREO",
                "SPATIAL_LEVEL_STEREO_IMBALANCE" in spatial_codes,
                SourceAnalysisCode.SPATIAL_CORRELATION,
            ),
        )
        for code, first_code, second_code, supported, correlation_source in rules:
            first = domains.get(first_code)
            second = domains.get(second_code)
            if supported and first is not None and second is not None:
                result.append(
                    cls._correlation(
                        code,
                        first,
                        second,
                        extra_sources=(correlation_source,),
                    )
                )

        drr_rules = (
            (
                GlobalCorrelationCode.LOW_DRR_DECAY_INTERACTION,
                GlobalDomainCode.RT60,
                "LOW_DRR_HIGH_RT60" in drr_codes,
            ),
            (
                GlobalCorrelationCode.DRR_EARLY_REFLECTION_INTERACTION,
                GlobalDomainCode.ETC,
                "LOW_DRR_DOMINANT_EARLY_REFLECTIONS" in drr_codes,
            ),
            (
                GlobalCorrelationCode.DRR_SPATIAL_ASYMMETRY,
                GlobalDomainCode.SPATIAL,
                "DRR_SPATIAL_CHANNEL_ASYMMETRY" in drr_codes,
            ),
        )
        drr_domain = domains.get(GlobalDomainCode.DIRECT_REVERBERANT)
        for code, other_code, supported in drr_rules:
            other = domains.get(other_code)
            if supported and drr_domain is not None and other is not None:
                result.append(
                    cls._correlation(
                        code,
                        drr_domain,
                        other,
                        extra_sources=(
                            SourceAnalysisCode.DIRECT_REVERBERANT_CORRELATION,
                        ),
                    )
                )

    @staticmethod
    def _codes(analysis):
        return (
            {item.code for item in analysis.correlations}
            if analysis is not None
            else set()
        )

    @classmethod
    def _both_priorities(cls, first, second) -> bool:
        return (
            first is not None
            and second is not None
            and first.score < cls.PRIORITY_SCORE_THRESHOLD
            and second.score < cls.PRIORITY_SCORE_THRESHOLD
        )

    @staticmethod
    def _correlation(
        code,
        first,
        second,
        *,
        extra_sources=(),
    ) -> GlobalCorrelation:
        return GlobalCorrelation(
            code=code,
            domain_codes=(first.code, second.code),
            source_analyses=(
                first.source_analysis,
                second.source_analysis,
                *extra_sources,
            ),
            score=min(first.score, second.score),
        )

    @staticmethod
    def _classification_code(item) -> str:
        return getattr(item.classification, "value", item.classification)
