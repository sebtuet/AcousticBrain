from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedExperimentCandidate:
    candidate_id: str
    hypothesis_code: str
    informative_value: float
    difficulty: str
    reversibility: str
    estimated_duration_minutes: int | None
    cost_category: str
    objective_code: str
    observable_fact_codes: tuple[str, ...]
    prerequisite_codes: tuple[str, ...]
    unmet_prerequisite_codes: tuple[str, ...]
    primary_selection_reason: str | None
    eligible: bool
    ineligibility_reasons: tuple[str, ...]


@dataclass(frozen=True)
class PresentedExperimentPlanning:
    status: str
    recommended_candidate: PresentedExperimentCandidate | None
    alternatives: tuple[PresentedExperimentCandidate, ...]
    all_candidates: tuple[PresentedExperimentCandidate, ...]
    applied_rule_codes: tuple[str, ...]
    technical_confidence: float | None
    source_analysis_codes: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


class ExperimentPlanningPresenter:
    """Projette le plan calculé sans classer ni enrichir les candidats."""

    STANDARD_ALTERNATIVE_COUNT = 3

    def present(self, context) -> PresentedExperimentPlanning | None:
        analysis = context.experiment_planning_analysis
        if analysis is None:
            return None
        plan = analysis.plan
        return PresentedExperimentPlanning(
            status=analysis.status.value,
            recommended_candidate=(
                self._candidate(plan.recommended_candidate)
                if plan.recommended_candidate is not None
                else None
            ),
            alternatives=tuple(
                self._candidate(item)
                for item in plan.ordered_candidates[1 : 1 + self.STANDARD_ALTERNATIVE_COUNT]
            ),
            all_candidates=tuple(
                self._candidate(item)
                for item in (
                    *plan.ordered_candidates,
                    *plan.ineligible_candidates,
                )
            ),
            applied_rule_codes=plan.applied_rule_codes,
            technical_confidence=plan.technical_confidence,
            source_analysis_codes=plan.source_analysis_codes,
        )

    @staticmethod
    def _candidate(candidate):
        return PresentedExperimentCandidate(
            candidate_id=candidate.candidate_id,
            hypothesis_code=candidate.hypothesis_code,
            informative_value=candidate.informative_value,
            difficulty=candidate.difficulty.name,
            reversibility=candidate.reversibility.name,
            estimated_duration_minutes=candidate.estimated_duration_minutes,
            cost_category=candidate.cost_category.name,
            objective_code=candidate.objective_code,
            observable_fact_codes=candidate.observable_fact_codes,
            prerequisite_codes=candidate.prerequisite_codes,
            unmet_prerequisite_codes=candidate.unmet_prerequisite_codes,
            primary_selection_reason=(
                candidate.selection_reasons[0].value
                if candidate.selection_reasons
                else None
            ),
            eligible=candidate.eligible,
            ineligibility_reasons=tuple(
                item.value for item in candidate.ineligibility_reasons
            ),
        )
