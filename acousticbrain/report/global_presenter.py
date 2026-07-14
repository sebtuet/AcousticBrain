from dataclasses import dataclass, field


@dataclass(frozen=True)
class PresentedGlobalDomain:
    code: str
    score: float
    confidence: float | None
    source_analysis: str
    recommendation_codes: tuple[str, ...] = ()
    recommendation_statuses: tuple[tuple[str, str], ...] = ()
    kind: str = "ACOUSTIC"
    contributes_to_acoustic_score: bool = True


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
    readiness_statuses: tuple[tuple[str, str], ...] = ()


class GlobalPresenter:
    """Projette la synthèse globale existante sans l'interpréter."""

    def present(self, context) -> PresentedGlobalAnalysis | None:
        analysis = context.global_analysis
        if analysis is None:
            return None

        recommendation_analysis = getattr(context, "recommendation_analysis", None)
        recommendation_statuses = {
            item.code: item.status.value
            for item in (
                recommendation_analysis.recommendations
                if recommendation_analysis is not None else ()
            )
        }
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
                    recommendation_statuses=tuple(
                        (code, recommendation_statuses.get(code, "ACTIVE"))
                        for code in domain.recommendation_codes
                    ),
                    kind=domain.kind.value,
                    contributes_to_acoustic_score=(
                        domain.contributes_to_acoustic_score
                    ),
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
            readiness_statuses=tuple(
                (item.family.value, item.status.value)
                for item in getattr(
                    context.measurement_readiness_analysis,
                    "analyses",
                    (),
                )
            ),
        )
