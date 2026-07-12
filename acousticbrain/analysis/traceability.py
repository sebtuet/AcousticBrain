from __future__ import annotations

from typing import TYPE_CHECKING

from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayCorrelationAnalysis,
    BinauralSpatialInterpretation,
    ClarityAnalysis,
    ClarityCorrelationAnalysis,
    DirectReverberantAnalysis,
    DirectReverberantCorrelationAnalysis,
    ETCAnalysis,
    ETCReflectionCorrelationAnalysis,
    EvidenceLevel,
    EvidenceReference,
    ExplanationLink,
    RT60Analysis,
    SpatialAnalysis,
    SpatialCorrelationAnalysis,
    SpeakerPairSpatialInterpretation,
    TraceabilityAnalysis,
)
from acousticbrain.knowledge_codes import FactCode, SourceAnalysisCode

if TYPE_CHECKING:
    from acousticbrain.models import (
        ConfidenceAnalysis,
        GlobalAnalysis,
        RecommendationAnalysis,
    )


class TraceabilityEngine:
    """Construit un graphe explicable à partir de connaissances structurées."""

    CLARITY_THRESHOLDS = (
        ("left_right_c50_differences_db", 2.0),
        ("left_right_c80_differences_db", 2.0),
        ("left_right_d50_differences_percent", 15.0),
        ("left_right_ts_differences_s", 0.02),
    )

    def analyze(
        self,
        *,
        global_analysis: GlobalAnalysis,
        recommendation_analysis: RecommendationAnalysis,
        rt60: RT60Analysis | None = None,
        etc: ETCAnalysis | None = None,
        clarity: ClarityAnalysis | None = None,
        spatial: SpatialAnalysis | None = None,
        spatial_interpretation: (
            SpeakerPairSpatialInterpretation
            | BinauralSpatialInterpretation
            | None
        ) = None,
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
    ) -> TraceabilityAnalysis:
        domain_evidence = {
            domain.source_analysis: EvidenceReference(
                code=self._evidence_code(domain.code),
                source_analysis=SourceAnalysisCode.GLOBAL,
                fact_code=self._fact_code(domain.code),
                evidence_level=EvidenceLevel.CALCULATED,
                value=domain.score,
            )
            for domain in global_analysis.domains
        }
        evidence_references = list(domain_evidence.values())
        physical_evidence = self._physical_evidence(
            rt60=rt60,
            etc=etc,
            clarity=clarity,
            spatial=spatial,
            spatial_interpretation=spatial_interpretation,
            clarity_correlations=clarity_correlations,
            spatial_correlations=spatial_correlations,
            etc_reflection_correlations=etc_reflection_correlations,
            direct_reverberant=direct_reverberant,
            direct_reverberant_correlations=(
                direct_reverberant_correlations
            ),
            bass_decay=bass_decay,
            bass_decay_correlations=bass_decay_correlations,
        )
        evidence_references.extend(physical_evidence)
        for item in physical_evidence:
            # La première preuve déclarée est le fait physique principal du
            # domaine ; les liens spécialisés peuvent sélectionner un fait
            # plus précis dans _recommendation_links.
            current = domain_evidence.get(item.source_analysis)
            if (
                current is None
                or current.source_analysis == SourceAnalysisCode.GLOBAL
            ):
                domain_evidence[item.source_analysis] = item
        links = self._correlation_links(global_analysis, domain_evidence)
        links.extend(
            self._recommendation_links(
                global_analysis,
                recommendation_analysis,
                domain_evidence,
                evidence_references,
            )
        )

        if confidence is not None:
            confidence_evidence = EvidenceReference(
                code="evidence.global.confidence",
                source_analysis="ConfidenceAnalysis",
                fact_code="global.confidence",
                evidence_level=EvidenceLevel.CALCULATED,
                value=confidence.score,
            )
            evidence_references.append(confidence_evidence)
            links.append(
                ExplanationLink(
                    code="explanation.global.confidence",
                    fact_codes=(confidence_evidence.fact_code,),
                    evidence_codes=(confidence_evidence.code,),
                )
            )

        recommendation_sources = (
            source
            for recommendation in recommendation_analysis.recommendations
            for source in recommendation.source_analyses
        )
        sources = tuple(
            dict.fromkeys(
                (
                    "GlobalAnalysis",
                    "RecommendationAnalysis",
                    *global_analysis.source_analyses,
                    *recommendation_sources,
                    *(item.source_analysis for item in physical_evidence),
                    *(("ConfidenceAnalysis",) if confidence is not None else ()),
                )
            )
        )

        return TraceabilityAnalysis(
            evidence_references=evidence_references,
            links=links,
            source_analyses=sources,
        )

    @classmethod
    def _physical_evidence(
        cls,
        *,
        rt60,
        etc,
        clarity,
        spatial,
        spatial_interpretation,
        clarity_correlations,
        spatial_correlations,
        etc_reflection_correlations,
        direct_reverberant,
        direct_reverberant_correlations,
        bass_decay,
        bass_decay_correlations,
    ):
        evidence = []
        if rt60 is not None:
            reliable_count = sum(
                item.confidence >= 70.0
                and abs(item.difference_seconds) >= 0.2
                for item in rt60.left_right_band_differences
            )
            evidence.extend(
                [
                    cls._evidence(
                        "evidence.rt60.broadband_mean",
                        SourceAnalysisCode.RT60,
                        FactCode.RT60_BROADBAND_MEAN,
                        getattr(rt60, "broadband_rt60_seconds", None),
                    ),
                    cls._evidence(
                        "evidence.rt60.reliable_difference_count",
                        SourceAnalysisCode.RT60,
                        FactCode.RT60_RELIABLE_DIFFERENCE_COUNT,
                        reliable_count,
                    ),
                    cls._evidence(
                        "evidence.rt60.interchannel_homogeneity",
                        SourceAnalysisCode.RT60,
                        FactCode.RT60_INTERCHANNEL_HOMOGENEITY,
                        getattr(rt60, "interchannel_homogeneity", None),
                    ),
                ]
            )
        if etc is not None:
            specific_count = (
                etc.left_only_event_count + etc.right_only_event_count
            )
            evidence.append(
                cls._evidence(
                    "evidence.etc.channel_specific_event_count",
                    SourceAnalysisCode.ETC,
                    FactCode.ETC_CHANNEL_SPECIFIC_EVENT_COUNT,
                    specific_count,
                )
            )
        if clarity is not None:
            centers = {
                center
                for attribute, threshold in cls.CLARITY_THRESHOLDS
                for center, difference in getattr(clarity, attribute).items()
                if abs(difference) >= threshold
            }
            evidence.append(
                cls._evidence(
                    "evidence.clarity.channel_asymmetry_count",
                    SourceAnalysisCode.CLARITY,
                    FactCode.CLARITY_CHANNEL_ASYMMETRY_COUNT,
                    len(centers),
                )
            )
        if spatial is not None and spatial_interpretation is not None:
            stability = getattr(
                spatial_interpretation,
                "technical_center_stability",
                None,
            )
            evidence.append(
                cls._evidence(
                    "evidence.spatial.technical_center_stability",
                    SourceAnalysisCode.SPATIAL,
                    FactCode.SPATIAL_TECHNICAL_CENTER_STABILITY,
                    getattr(stability, "value", "BINAURAL"),
                )
            )
        if clarity_correlations is not None:
            evidence.append(
                cls._evidence(
                    "evidence.clarity.correlation_count",
                    SourceAnalysisCode.CLARITY_CORRELATION,
                    FactCode.CLARITY_CORRELATION_COUNT,
                    len(clarity_correlations.correlations),
                )
            )
        if spatial_correlations is not None:
            evidence.append(
                cls._evidence(
                    "evidence.spatial.correlation_count",
                    SourceAnalysisCode.SPATIAL_CORRELATION,
                    FactCode.SPATIAL_CORRELATION_COUNT,
                    len(spatial_correlations.correlations),
                )
            )
        if etc_reflection_correlations is not None:
            unmatched_count = sum(
                event.delay_ms <= 20.0 and event.relative_level_db >= -20.0
                for events in etc_reflection_correlations.unmatched_events.values()
                for event in events
            )
            evidence.append(
                cls._evidence(
                    "evidence.etc_reflection.dominant_unmatched_event_count",
                    SourceAnalysisCode.ETC_REFLECTION_CORRELATION,
                    FactCode.ETC_REFLECTION_DOMINANT_UNMATCHED_EVENT_COUNT,
                    unmatched_count,
                )
            )
        if direct_reverberant is not None:
            evidence.extend(
                [
                    cls._evidence(
                        "evidence.direct_reverberant.broadband_drr_db",
                        SourceAnalysisCode.DIRECT_REVERBERANT,
                        FactCode.DRR_BROADBAND_DB,
                        direct_reverberant.broadband_direct_to_reverberant_db,
                    ),
                    cls._evidence(
                        "evidence.direct_reverberant.asymmetric_band_count",
                        SourceAnalysisCode.DIRECT_REVERBERANT,
                        FactCode.DRR_ASYMMETRIC_BAND_COUNT,
                        sum(
                            abs(value) >= 3.0
                            for value in direct_reverberant.left_right_direct_to_reverberant_differences_db.values()
                        ),
                    ),
                ]
            )
        if direct_reverberant_correlations is not None:
            evidence.append(
                cls._evidence(
                    "evidence.direct_reverberant.correlation_count",
                    SourceAnalysisCode.DIRECT_REVERBERANT_CORRELATION,
                    FactCode.DRR_CORRELATION_COUNT,
                    len(direct_reverberant_correlations.correlations),
                )
            )
        if bass_decay is not None:
            times = [
                band.estimated_decay_time_seconds
                for band in bass_decay.aggregate_bands
                if band.estimated_decay_time_seconds is not None
            ]
            significant_count = sum(
                abs(item.difference_seconds) >= 0.25
                for item in bass_decay.left_right_band_differences
            )
            evidence.extend(
                [
                    cls._evidence(
                        "evidence.bass_decay.maximum_decay_time",
                        SourceAnalysisCode.BASS_DECAY,
                        FactCode.BASS_DECAY_MAXIMUM_DECAY_TIME,
                        max(times) if times else None,
                    ),
                    cls._evidence(
                        "evidence.bass_decay.usable_band_count",
                        SourceAnalysisCode.BASS_DECAY,
                        FactCode.BASS_DECAY_USABLE_BAND_COUNT,
                        len(times),
                    ),
                    cls._evidence(
                        "evidence.bass_decay.significant_difference_count",
                        SourceAnalysisCode.BASS_DECAY,
                        FactCode.BASS_DECAY_SIGNIFICANT_DIFFERENCE_COUNT,
                        significant_count,
                    ),
                ]
            )
        if bass_decay_correlations is not None:
            evidence.append(
                cls._evidence(
                    "evidence.bass_decay.correlation_count",
                    SourceAnalysisCode.BASS_DECAY_CORRELATION,
                    FactCode.BASS_DECAY_CORRELATION_COUNT,
                    len(bass_decay_correlations.correlations),
                )
            )
        return evidence

    @staticmethod
    def _evidence(code, source, fact, value):
        return EvidenceReference(
            code=code,
            source_analysis=source,
            fact_code=fact,
            evidence_level=EvidenceLevel.CALCULATED,
            value=value,
        )

    @classmethod
    def _correlation_links(cls, global_analysis, domain_evidence):
        links = []
        for correlation in global_analysis.correlations:
            evidence = [
                domain_evidence[source]
                for source in correlation.source_analyses
                if source in domain_evidence
            ]
            if len(evidence) != len(correlation.source_analyses):
                continue

            links.append(
                ExplanationLink(
                    code=f"explanation.correlation.{correlation.code.lower()}",
                    fact_codes=tuple(item.fact_code for item in evidence),
                    evidence_codes=tuple(item.code for item in evidence),
                    correlation_codes=(correlation.code,),
                )
            )
        return links

    @classmethod
    def _recommendation_links(
        cls,
        global_analysis,
        recommendation_analysis,
        domain_evidence,
        evidence_references,
    ):
        links = []
        evidence_by_code = {
            item.code: item for item in evidence_references
        }
        for recommendation in recommendation_analysis.recommendations:
            recommendation_evidence = dict(domain_evidence)
            if recommendation.code == "INVESTIGATE_DRR_CHANNEL_DIFFERENCES":
                asymmetric = evidence_by_code.get(
                    "evidence.direct_reverberant.asymmetric_band_count"
                )
                if asymmetric is not None:
                    recommendation_evidence[
                        SourceAnalysisCode.DIRECT_REVERBERANT
                    ] = asymmetric
            if recommendation.code == "IMPROVE_DIRECT_SOUND_DOMINANCE":
                broadband = evidence_by_code.get(
                    "evidence.direct_reverberant.broadband_drr_db"
                )
                if broadband is not None:
                    recommendation_evidence[
                        SourceAnalysisCode.DIRECT_REVERBERANT
                    ] = broadband
            if recommendation.code == "INVESTIGATE_RT60_CHANNEL_DIFFERENCES":
                reliable = evidence_by_code.get(
                    "evidence.rt60.reliable_difference_count"
                )
                if reliable is not None:
                    recommendation_evidence[SourceAnalysisCode.RT60] = reliable
            if recommendation.code == "COMPARE_BASS_DECAY_CHANNELS":
                differences = evidence_by_code.get(
                    "evidence.bass_decay.significant_difference_count"
                )
                if differences is not None:
                    recommendation_evidence[
                        SourceAnalysisCode.BASS_DECAY
                    ] = differences
            evidence = [
                recommendation_evidence[source]
                for source in recommendation.source_analyses
                if source in recommendation_evidence
            ]
            if (
                not evidence
                or len(evidence) != len(recommendation.source_analyses)
            ):
                continue

            recommendation_sources = set(recommendation.source_analyses)
            correlation_codes = tuple(
                correlation.code
                for correlation in global_analysis.correlations
                if set(correlation.source_analyses).issubset(recommendation_sources)
            )
            links.append(
                ExplanationLink(
                    code=(
                        "explanation.recommendation."
                        f"{recommendation.code.lower()}"
                    ),
                    fact_codes=tuple(item.fact_code for item in evidence),
                    evidence_codes=tuple(item.code for item in evidence),
                    correlation_codes=correlation_codes,
                    recommendation_codes=(recommendation.code,),
                )
            )
        return links

    @staticmethod
    def _evidence_code(domain_code: str) -> str:
        return f"evidence.global.domain.{domain_code.lower()}.score"

    @staticmethod
    def _fact_code(domain_code: str) -> str:
        return f"global.domain.{domain_code.lower()}.score"
