from dataclasses import dataclass, field


@dataclass(frozen=True)
class PresentedGlobalDomain:
    code: str
    score: float
    confidence: float | None
    source_analysis: str
    recommendation_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PresentedGlobalCorrelation:
    code: str
    domain_codes: tuple[str, ...]
    source_analyses: tuple[str, ...]
    score: float


@dataclass
class PresentedGlobalAnalysis:
    score: float | None
    confidence: float | None
    domains: list[PresentedGlobalDomain] = field(default_factory=list)
    correlations: list[PresentedGlobalCorrelation] = field(default_factory=list)
    priority_domains: tuple[str, ...] = ()
    source_analyses: tuple[str, ...] = ()


class GlobalPresenter:
    """Projette la synthèse globale existante sans l'interpréter."""

    def present(self, context) -> PresentedGlobalAnalysis | None:
        analysis = context.global_analysis
        if analysis is None:
            return None

        return PresentedGlobalAnalysis(
            score=analysis.score,
            confidence=analysis.confidence,
            domains=[
                PresentedGlobalDomain(
                    code=domain.code,
                    score=domain.score,
                    confidence=domain.confidence,
                    source_analysis=domain.source_analysis,
                    recommendation_codes=domain.recommendation_codes,
                )
                for domain in analysis.domains
            ],
            correlations=[
                PresentedGlobalCorrelation(
                    code=correlation.code,
                    domain_codes=correlation.domain_codes,
                    source_analyses=correlation.source_analyses,
                    score=correlation.score,
                )
                for correlation in analysis.correlations
            ],
            priority_domains=analysis.priority_domains,
            source_analyses=analysis.source_analyses,
        )

