from dataclasses import asdict, dataclass, field

from acousticbrain.models import EvidenceValue


@dataclass(frozen=True)
class PresentedEvidenceReference:
    code: str
    source_analysis: str
    fact_code: str
    evidence_level: str
    value: EvidenceValue | None = None


@dataclass(frozen=True)
class PresentedExplanationLink:
    code: str
    fact_codes: tuple[str, ...]
    evidence_codes: tuple[str, ...]
    correlation_codes: tuple[str, ...] = ()
    recommendation_codes: tuple[str, ...] = ()


@dataclass
class PresentedTraceabilityAnalysis:
    evidence_references: list[PresentedEvidenceReference] = field(
        default_factory=list
    )
    links: list[PresentedExplanationLink] = field(default_factory=list)
    source_analyses: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        """Retourne uniquement des primitives directement sérialisables."""

        return asdict(self)


class TraceabilityPresenter:
    """Projette le graphe existant sans résoudre ni créer de liens."""

    def present(self, context) -> PresentedTraceabilityAnalysis | None:
        analysis = context.traceability_analysis
        if analysis is None:
            return None

        return PresentedTraceabilityAnalysis(
            evidence_references=[
                PresentedEvidenceReference(
                    code=evidence.code,
                    source_analysis=evidence.source_analysis,
                    fact_code=evidence.fact_code,
                    evidence_level=evidence.evidence_level.value,
                    value=evidence.value,
                )
                for evidence in analysis.evidence_references
            ],
            links=[
                PresentedExplanationLink(
                    code=link.code,
                    fact_codes=link.fact_codes,
                    evidence_codes=link.evidence_codes,
                    correlation_codes=link.correlation_codes,
                    recommendation_codes=link.recommendation_codes,
                )
                for link in analysis.links
            ],
            source_analyses=analysis.source_analyses,
        )

