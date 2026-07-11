from __future__ import annotations

from typing import TYPE_CHECKING

from acousticbrain.models import (
    EvidenceLevel,
    EvidenceReference,
    ExplanationLink,
    TraceabilityAnalysis,
)

if TYPE_CHECKING:
    from acousticbrain.models import (
        ConfidenceAnalysis,
        GlobalAnalysis,
        RecommendationAnalysis,
    )


class TraceabilityEngine:
    """Construit un graphe explicable à partir de connaissances structurées."""

    def analyze(
        self,
        *,
        global_analysis: GlobalAnalysis,
        recommendation_analysis: RecommendationAnalysis,
        confidence: ConfidenceAnalysis | None = None,
    ) -> TraceabilityAnalysis:
        domain_evidence = {
            domain.source_analysis: EvidenceReference(
                code=self._evidence_code(domain.code),
                source_analysis=domain.source_analysis,
                fact_code=self._fact_code(domain.code),
                evidence_level=EvidenceLevel.CALCULATED,
                value=domain.score,
            )
            for domain in global_analysis.domains
        }
        evidence_references = list(domain_evidence.values())
        links = self._correlation_links(global_analysis, domain_evidence)
        links.extend(
            self._recommendation_links(
                global_analysis,
                recommendation_analysis,
                domain_evidence,
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
    ):
        links = []
        for recommendation in recommendation_analysis.recommendations:
            evidence = [
                domain_evidence[source]
                for source in recommendation.source_analyses
                if source in domain_evidence
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
        return f"evidence.{domain_code.lower()}.score"

    @staticmethod
    def _fact_code(domain_code: str) -> str:
        return f"{domain_code.lower()}.score"
