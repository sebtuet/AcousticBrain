from __future__ import annotations

from statistics import fmean
from typing import TYPE_CHECKING

from acousticbrain.models import (
    GlobalAnalysis,
    GlobalCorrelation,
    GlobalDomainAnalysis,
    ModalDensityAnalysis,
    SBIRAnalysis,
    StereoAnalysis,
)

if TYPE_CHECKING:
    from acousticbrain.models import ConfidenceAnalysis, PeakClassificationAnalysis


class GlobalSynthesizer:
    """Agrège exclusivement des connaissances d'analyse structurées."""

    PRIORITY_SCORE_THRESHOLD = 85.0

    def synthesize(
        self,
        *,
        stereo: StereoAnalysis | None = None,
        sbir: SBIRAnalysis | None = None,
        modal_density: ModalDensityAnalysis | None = None,
        peak_classification: PeakClassificationAnalysis | None = None,
        confidence: ConfidenceAnalysis | None = None,
    ) -> GlobalAnalysis:
        domains = self._domains(
            stereo=stereo,
            sbir=sbir,
            modal_density=modal_density,
            peak_classification=peak_classification,
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
            correlations=self._correlations(domains, peak_classification),
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

        return domains

    @classmethod
    def _correlations(
        cls,
        domains: list[GlobalDomainAnalysis],
        peak_classification: PeakClassificationAnalysis | None,
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

        return correlations

    @classmethod
    def _both_priorities(cls, first, second) -> bool:
        return (
            first is not None
            and second is not None
            and first.score < cls.PRIORITY_SCORE_THRESHOLD
            and second.score < cls.PRIORITY_SCORE_THRESHOLD
        )

    @staticmethod
    def _correlation(code, first, second) -> GlobalCorrelation:
        return GlobalCorrelation(
            code=code,
            domain_codes=(first.code, second.code),
            source_analyses=(first.source_analysis, second.source_analysis),
            score=min(first.score, second.score),
        )

    @staticmethod
    def _classification_code(item) -> str:
        return getattr(item.classification, "value", item.classification)

