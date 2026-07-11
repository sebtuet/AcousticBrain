from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from acousticbrain.models import (
    ModalDensityAnalysis,
    Recommendation,
    RecommendationAnalysis,
    RecommendationPriority,
    SBIRAnalysis,
    StereoAnalysis,
)

if TYPE_CHECKING:
    from acousticbrain.models import ConfidenceAnalysis, PeakClassificationAnalysis


class RecommendationEngine:
    """Déduit des actions structurées à partir des seules analyses physiques."""

    def analyze(
        self,
        *,
        stereo: StereoAnalysis | None = None,
        sbir: SBIRAnalysis | None = None,
        modal_density: ModalDensityAnalysis | None = None,
        peak_classification: PeakClassificationAnalysis | None = None,
        confidence: ConfidenceAnalysis | None = None,
    ) -> RecommendationAnalysis:
        recommendations: list[Recommendation] = []

        if stereo is not None:
            recommendations.extend(self._from_stereo(stereo))
        if sbir is not None:
            recommendations.extend(self._from_sbir(sbir))
        if modal_density is not None:
            recommendations.extend(self._from_modal_density(modal_density))
        if peak_classification is not None:
            recommendations.extend(self._from_peak_classification(peak_classification))

        if confidence is not None:
            recommendations = [
                replace(item, confidence=min(item.confidence, confidence.score))
                for item in recommendations
            ]

        return RecommendationAnalysis(
            recommendations=self._deduplicate(recommendations)
        )

    @staticmethod
    def _from_stereo(analysis: StereoAnalysis) -> list[Recommendation]:
        balances = [
            abs(balance)
            for balance in (
                analysis.balance_low,
                analysis.balance_mid,
                analysis.balance_high,
            )
            if balance is not None
        ]
        maximum_balance = max(balances, default=0.0)

        if analysis.symmetry_score >= 70.0 and maximum_balance <= 1.0:
            return []

        return [
            Recommendation(
                code="CHECK_STEREO_PLACEMENT",
                action="check_placement",
                target="stereo_speakers",
                priority=(
                    RecommendationPriority.HIGH
                    if analysis.symmetry_score < 40.0 or maximum_balance > 3.0
                    else RecommendationPriority.MEDIUM
                ),
                confidence=90.0,
                source_analyses=("StereoAnalysis",),
                parameters={
                    "symmetry_score": analysis.symmetry_score,
                    "maximum_balance_db": maximum_balance,
                },
            )
        ]

    @staticmethod
    def _from_sbir(analysis: SBIRAnalysis) -> list[Recommendation]:
        candidate = analysis.best_match
        if candidate is None:
            return []

        return [
            Recommendation(
                code="TEST_SPEAKER_DISTANCE",
                action="test_distance",
                target=candidate.surface.name.lower(),
                priority=(
                    RecommendationPriority.HIGH
                    if analysis.score < 60.0
                    else RecommendationPriority.MEDIUM
                ),
                confidence=analysis.confidence,
                source_analyses=("SBIRAnalysis",),
                parameters={
                    "current_distance_m": candidate.distance_m,
                    "measured_frequency_hz": candidate.measured_frequency,
                },
            )
        ]

    @staticmethod
    def _from_modal_density(
        analysis: ModalDensityAnalysis,
    ) -> list[Recommendation]:
        if not analysis.sparse_bands and not analysis.dense_bands:
            return []

        return [
            Recommendation(
                code="MEASURE_MULTIPLE_POSITIONS",
                action="measure",
                target="listening_area",
                priority=(
                    RecommendationPriority.HIGH
                    if analysis.score < 60.0
                    else RecommendationPriority.MEDIUM
                ),
                confidence=analysis.confidence,
                source_analyses=("ModalDensityAnalysis",),
                parameters={
                    "sparse_band_count": len(analysis.sparse_bands),
                    "dense_band_count": len(analysis.dense_bands),
                },
            )
        ]

    @staticmethod
    def _from_peak_classification(
        analysis: PeakClassificationAnalysis,
    ) -> list[Recommendation]:
        unclassified_count = sum(
            getattr(item.classification, "value", item.classification)
            == "UNCLASSIFIED"
            for item in analysis.classifications
        )
        if unclassified_count == 0:
            return []

        shared = {
            "priority": RecommendationPriority.MEDIUM,
            "confidence": analysis.confidence,
            "source_analyses": ("PeakClassificationAnalysis",),
            "parameters": {"unclassified_peak_count": unclassified_count},
        }
        return [
            Recommendation(
                code="INVESTIGATE_UNCLASSIFIED_PEAKS",
                action="investigate",
                target="unclassified_peaks",
                **shared,
            ),
            Recommendation(
                code="MEASURE_MULTIPLE_POSITIONS",
                action="measure",
                target="listening_area",
                **shared,
            ),
        ]

    @staticmethod
    def _deduplicate(
        recommendations: list[Recommendation],
    ) -> list[Recommendation]:
        by_code: dict[str, Recommendation] = {}

        for recommendation in recommendations:
            existing = by_code.get(recommendation.code)
            if existing is None:
                by_code[recommendation.code] = recommendation
                continue

            parameters = dict(existing.parameters)
            for name, value in recommendation.parameters.items():
                parameters.setdefault(name, value)

            by_code[recommendation.code] = replace(
                existing,
                priority=max(existing.priority, recommendation.priority),
                confidence=max(existing.confidence, recommendation.confidence),
                source_analyses=tuple(
                    dict.fromkeys(
                        existing.source_analyses + recommendation.source_analyses
                    )
                ),
                parameters=parameters,
            )

        return list(by_code.values())

