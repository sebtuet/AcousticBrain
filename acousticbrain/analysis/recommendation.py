from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayCorrelationAnalysis,
    ClarityCorrelationAnalysis,
    ETCAnalysis,
    ETCReflectionCorrelationAnalysis,
    DirectReverberantAnalysis,
    DirectReverberantCorrelationAnalysis,
    ModalDensityAnalysis,
    Recommendation,
    RecommendationAnalysis,
    RecommendationPriority,
    RT60Analysis,
    SBIRAnalysis,
    SpatialAnalysis,
    SpatialCorrelationAnalysis,
    StereoAnalysis,
)
from acousticbrain.knowledge_codes import RecommendationCode, SourceAnalysisCode

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
        rt60: RT60Analysis | None = None,
        etc: ETCAnalysis | None = None,
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
        bass_decay: BassDecayAnalysis | None = None,
        bass_decay_correlations: BassDecayCorrelationAnalysis | None = None,
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
        if rt60 is not None:
            recommendations.extend(self._from_rt60(rt60))
        if etc is not None:
            recommendations.extend(self._from_etc_symmetry(etc))
        if spatial is not None:
            recommendations.extend(self._from_spatial(spatial))
        if clarity_correlations is not None:
            recommendations.extend(
                self._from_clarity_correlations(clarity_correlations)
            )
        if spatial_correlations is not None:
            recommendations.extend(
                self._from_spatial_correlations(spatial_correlations)
            )
        if etc_reflection_correlations is not None:
            recommendations.extend(
                self._from_etc_reflections(etc_reflection_correlations)
            )
        if direct_reverberant is not None:
            recommendations.extend(
                self._from_direct_reverberant(direct_reverberant)
            )
        if direct_reverberant_correlations is not None:
            recommendations.extend(
                self._from_direct_reverberant_correlations(
                    direct_reverberant_correlations
                )
            )
        if bass_decay is not None and bass_decay_correlations is not None:
            recommendations.extend(
                self._from_bass_decay(bass_decay, bass_decay_correlations)
            )

        if confidence is not None:
            recommendations = [
                replace(item, confidence=min(item.confidence, confidence.score))
                for item in recommendations
            ]

        return RecommendationAnalysis(
            recommendations=self._deduplicate(recommendations)
        )

    @staticmethod
    def _from_bass_decay(analysis, correlations):
        by_code = {item.code: item for item in correlations.correlations}
        recommendations = []
        long_codes = {
            "SLOW_DECAY_MODAL_INTERACTION",
            "SLOW_DECAY_RT60_INTERACTION",
            "LOW_DRR_LONG_BASS_DECAY",
        }
        long_items = [
            item for code, item in by_code.items() if code in long_codes
        ]
        if long_items:
            recommendations.append(
                Recommendation(
                    code=RecommendationCode.INVESTIGATE_LONG_BASS_DECAY,
                    action="investigate",
                    target="bass_decay_bands",
                    priority=RecommendationPriority.HIGH,
                    confidence=min(
                        analysis.confidence,
                        max(item.confidence for item in long_items),
                    ),
                    source_analyses=(
                        SourceAnalysisCode.BASS_DECAY,
                        SourceAnalysisCode.BASS_DECAY_CORRELATION,
                    ),
                    parameters={
                        "supporting_correlation_count": len(long_items),
                        "maximum_decay_time_s": max(
                            item.source_metrics["maximum_decay_time_s"]
                            for item in long_items
                        ),
                    },
                )
            )
        modal = by_code.get("SLOW_DECAY_MODAL_INTERACTION")
        if modal is not None:
            recommendations.append(
                Recommendation(
                    code=RecommendationCode.CHECK_MODAL_EXCITATION,
                    action="check",
                    target="modal_excitation",
                    priority=RecommendationPriority.HIGH,
                    confidence=min(analysis.confidence, modal.confidence),
                    source_analyses=(
                        SourceAnalysisCode.BASS_DECAY,
                        SourceAnalysisCode.BASS_DECAY_CORRELATION,
                    ),
                    parameters={
                        "matched_mode_count": modal.source_metrics[
                            "matched_mode_count"
                        ],
                    },
                )
            )
        asymmetric = by_code.get("ASYMMETRIC_BASS_DECAY")
        if asymmetric is not None:
            recommendations.append(
                Recommendation(
                    code=RecommendationCode.COMPARE_BASS_DECAY_CHANNELS,
                    action="compare",
                    target="bass_decay_channels",
                    priority=RecommendationPriority.MEDIUM,
                    confidence=min(analysis.confidence, asymmetric.confidence),
                    source_analyses=(
                        SourceAnalysisCode.BASS_DECAY,
                        SourceAnalysisCode.BASS_DECAY_CORRELATION,
                    ),
                    parameters={
                        "significant_band_count": int(
                            asymmetric.source_metrics[
                                "asymmetric_band_count"
                            ]
                        ),
                        "maximum_difference_s": asymmetric.source_metrics[
                            "maximum_left_right_difference_s"
                        ],
                    },
                )
            )
        return recommendations

    @staticmethod
    def _from_direct_reverberant(
        analysis: DirectReverberantAnalysis,
    ) -> list[Recommendation]:
        recommendations = []
        broadband = analysis.broadband_direct_to_reverberant_db
        if broadband is not None and broadband < 0.0:
            recommendations.append(
                Recommendation(
                    code=RecommendationCode.IMPROVE_DIRECT_SOUND_DOMINANCE,
                    action="improve_dominance",
                    target="direct_sound",
                    priority=RecommendationPriority.HIGH,
                    confidence=analysis.confidence,
                    source_analyses=(
                        SourceAnalysisCode.DIRECT_REVERBERANT,
                    ),
                    parameters={"broadband_drr_db": broadband},
                )
            )
        significant = {
            center: difference
            for center, difference in (
                analysis.left_right_direct_to_reverberant_differences_db.items()
            )
            if abs(difference) >= 3.0
        }
        if significant:
            recommendations.append(
                Recommendation(
                    code=(
                        RecommendationCode.INVESTIGATE_DRR_CHANNEL_DIFFERENCES
                    ),
                    action="investigate",
                    target="drr_channel_differences",
                    priority=(
                        RecommendationPriority.HIGH
                        if len(significant) >= 3
                        else RecommendationPriority.MEDIUM
                    ),
                    confidence=analysis.confidence,
                    source_analyses=(
                        SourceAnalysisCode.DIRECT_REVERBERANT,
                    ),
                    parameters={
                        "significant_band_count": len(significant),
                        "maximum_difference_db": max(
                            abs(value) for value in significant.values()
                        ),
                    },
                )
            )
        return recommendations

    @staticmethod
    def _from_direct_reverberant_correlations(analysis):
        codes = {item.code for item in analysis.correlations}
        recommendations = []
        if codes & {
            "LOW_DRR_HIGH_RT60",
            "LOW_DRR_DOMINANT_EARLY_REFLECTIONS",
        }:
            supported = [
                item
                for item in analysis.correlations
                if item.code
                in {
                    "LOW_DRR_HIGH_RT60",
                    "LOW_DRR_DOMINANT_EARLY_REFLECTIONS",
                }
            ]
            recommendations.append(
                Recommendation(
                    code=RecommendationCode.IMPROVE_DIRECT_SOUND_DOMINANCE,
                    action="improve_dominance",
                    target="direct_sound",
                    priority=RecommendationPriority.HIGH,
                    confidence=max(item.confidence for item in supported),
                    source_analyses=(
                        SourceAnalysisCode.DIRECT_REVERBERANT,
                        SourceAnalysisCode.DIRECT_REVERBERANT_CORRELATION,
                    ),
                    parameters={
                        "supporting_correlation_count": len(supported)
                    },
                )
            )
        dominant = [
            item
            for item in analysis.correlations
            if item.code == "LOW_DRR_DOMINANT_EARLY_REFLECTIONS"
        ]
        if dominant:
            recommendations.append(
                Recommendation(
                    code=RecommendationCode.APPLY_EARLY_REFLECTION_TREATMENT,
                    action="apply_treatment",
                    target="dominant_early_reflections",
                    priority=RecommendationPriority.HIGH,
                    confidence=max(item.confidence for item in dominant),
                    source_analyses=(
                        SourceAnalysisCode.DIRECT_REVERBERANT,
                        SourceAnalysisCode.ETC,
                        SourceAnalysisCode.DIRECT_REVERBERANT_CORRELATION,
                    ),
                    parameters={
                        "supporting_correlation_count": len(dominant)
                    },
                )
            )
        return recommendations

    @staticmethod
    def _from_rt60(analysis: RT60Analysis) -> list[Recommendation]:
        reliable = [
            item
            for item in analysis.left_right_band_differences
            if item.confidence >= 70.0
            and abs(item.difference_seconds) >= 0.2
        ]
        if not reliable:
            return []
        maximum = max(abs(item.difference_seconds) for item in reliable)
        return [
            Recommendation(
                code=RecommendationCode.INVESTIGATE_RT60_CHANNEL_DIFFERENCES,
                action="investigate",
                target="rt60_channel_differences",
                priority=(
                    RecommendationPriority.HIGH
                    if len(reliable) >= 3 or maximum >= 1.0
                    else RecommendationPriority.MEDIUM
                ),
                confidence=min(item.confidence for item in reliable),
                source_analyses=(SourceAnalysisCode.RT60,),
                parameters={
                    "reliable_band_count": len(reliable),
                    "maximum_difference_s": maximum,
                },
            )
        ]

    @staticmethod
    def _from_etc_symmetry(analysis: ETCAnalysis) -> list[Recommendation]:
        difference = abs(
            analysis.left_only_event_count - analysis.right_only_event_count
        )
        if difference < 3:
            return []
        return [
            Recommendation(
                code=RecommendationCode.CHECK_EARLY_REFLECTION_SYMMETRY,
                action="check_symmetry",
                target="early_reflections",
                priority=RecommendationPriority.MEDIUM,
                confidence=analysis.confidence,
                source_analyses=(SourceAnalysisCode.ETC,),
                parameters={
                    "specific_event_count_difference": difference,
                },
            )
        ]

    @staticmethod
    def _from_etc_reflections(
        analysis: ETCReflectionCorrelationAnalysis,
    ) -> list[Recommendation]:
        important = [
            event
            for events in analysis.unmatched_events.values()
            for event in events
            if event.delay_ms <= 20.0 and event.relative_level_db >= -20.0
        ]
        if not important:
            return []
        return [
            Recommendation(
                code=RecommendationCode.INVESTIGATE_DOMINANT_EARLY_REFLECTIONS,
                action="investigate",
                target="dominant_early_reflections",
                priority=(
                    RecommendationPriority.HIGH
                    if len(important) >= 3
                    else RecommendationPriority.MEDIUM
                ),
                confidence=min(event.confidence for event in important),
                source_analyses=(
                    SourceAnalysisCode.ETC,
                    SourceAnalysisCode.ETC_REFLECTION_CORRELATION,
                ),
                parameters={
                    "important_unmatched_event_count": len(important),
                    "maximum_relative_level_db": max(
                        event.relative_level_db for event in important
                    ),
                },
            )
        ]

    @staticmethod
    def _from_spatial(analysis: SpatialAnalysis) -> list[Recommendation]:
        pair = analysis.pair_analysis
        if (
            pair is None
            or pair.broadband_time_difference_ms is None
            or abs(pair.broadband_time_difference_ms) <= 0.2
        ):
            return []
        return [
            Recommendation(
                code=RecommendationCode.VERIFY_TIME_ALIGNMENT,
                action="verify_alignment",
                target="speaker_pair",
                priority=RecommendationPriority.MEDIUM,
                confidence=analysis.confidence,
                source_analyses=(SourceAnalysisCode.SPATIAL,),
                parameters={
                    "broadband_time_difference_ms": (
                        pair.broadband_time_difference_ms
                    ),
                },
            )
        ]

    @staticmethod
    def _from_clarity_correlations(
        analysis: ClarityCorrelationAnalysis,
    ) -> list[Recommendation]:
        supported = [
            item
            for item in analysis.correlations
            if item.code == "CLARITY_ETC_CHANNEL_ASYMMETRY"
        ]
        if not supported:
            return []
        return [
            Recommendation(
                code=RecommendationCode.CHECK_EARLY_REFLECTION_SYMMETRY,
                action="check_symmetry",
                target="early_reflections",
                priority=RecommendationPriority.HIGH,
                confidence=min(item.confidence for item in supported),
                source_analyses=(
                    SourceAnalysisCode.CLARITY,
                    SourceAnalysisCode.ETC,
                    SourceAnalysisCode.CLARITY_CORRELATION,
                ),
                parameters={
                    "supporting_correlation_count": len(supported),
                },
            )
        ]

    @staticmethod
    def _from_spatial_correlations(
        analysis: SpatialCorrelationAnalysis,
    ) -> list[Recommendation]:
        supported = [
            item
            for item in analysis.correlations
            if item.code == "SPATIAL_TIME_ETC_CHANNEL_IMBALANCE"
        ]
        if not supported:
            return []
        return [
            Recommendation(
                code=RecommendationCode.VERIFY_TIME_ALIGNMENT,
                action="verify_alignment",
                target="speaker_pair",
                priority=RecommendationPriority.HIGH,
                confidence=min(item.confidence for item in supported),
                source_analyses=(
                    SourceAnalysisCode.SPATIAL,
                    SourceAnalysisCode.ETC,
                    SourceAnalysisCode.SPATIAL_CORRELATION,
                ),
                parameters={
                    "supporting_correlation_count": len(supported),
                },
            )
        ]

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

            # Plusieurs preuves ne créent pas une confiance artificielle :
            # la fusion conserve la confiance locale la plus forte.
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
