from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedMaterialAwareReflectionCandidate:
    candidate_id: str
    correlation_id: str | None
    path_id: str
    surface_id: str
    region_id: str | None
    observed_event_id: str | None
    theoretical_delay_ms: float | None
    measured_delay_ms: float | None
    timing_error_ms: float | None
    geometric_temporal_score: float
    geometric_confidence: float | None
    geometric_status: str
    material_assessment: str
    material_confidence: float | None
    material_id: str | None
    assignment_id: str | None
    catalog_entry_id: str | None
    overall_compatibility_score: float
    informative_rank: int | None
    status: str
    causality_status: str
    eligibility_impact: str
    evidence_codes: tuple[str, ...]
    limitations: tuple[str, ...]
    provenance_codes: tuple[str, ...]


@dataclass(frozen=True)
class PresentedMaterialAwareReflectionCandidateAnalysis:
    candidates: tuple[PresentedMaterialAwareReflectionCandidate, ...]
    source_analysis_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]


class MaterialAwareReflectionCandidatePresenter:
    """Projects the leaf analysis and resolves timing through correlation IDs."""

    def present(self, context):
        analysis = context.material_aware_reflection_candidate_analysis
        if analysis is None or not analysis.candidates:
            return None
        correlations = {
            item.code: item
            for item in context.etc_reflection_correlation_analysis.correlations
        }
        return PresentedMaterialAwareReflectionCandidateAnalysis(
            candidates=tuple(
                self._candidate(item, correlations.get(item.correlation_id))
                for item in analysis.candidates
            ),
            source_analysis_codes=analysis.source_analysis_codes,
            applied_rule_codes=analysis.applied_rule_codes,
        )

    @staticmethod
    def _candidate(item, correlation):
        return PresentedMaterialAwareReflectionCandidate(
            candidate_id=item.candidate_id,
            correlation_id=item.correlation_id,
            path_id=item.path_id,
            surface_id=item.surface_id,
            region_id=item.region_id,
            observed_event_id=item.observed_event_id,
            theoretical_delay_ms=(
                correlation.theoretical_delay_ms if correlation is not None else None
            ),
            measured_delay_ms=(
                correlation.measured_delay_ms if correlation is not None else None
            ),
            timing_error_ms=(
                correlation.timing_error_ms if correlation is not None else None
            ),
            geometric_temporal_score=item.geometric_temporal_score,
            geometric_confidence=item.geometric_confidence,
            geometric_status=item.geometric_status.value,
            material_assessment=item.material_assessment.value,
            material_confidence=item.material_confidence,
            material_id=item.material_id,
            assignment_id=item.assignment_id,
            catalog_entry_id=item.catalog_entry_id,
            overall_compatibility_score=item.overall_compatibility_score,
            informative_rank=item.informative_rank,
            status=item.status.value,
            causality_status=item.causality_status.value,
            eligibility_impact=item.eligibility_impact.value,
            evidence_codes=tuple(link.code for link in item.evidence_links),
            limitations=item.limitations,
            provenance_codes=item.provenance_codes,
        )
